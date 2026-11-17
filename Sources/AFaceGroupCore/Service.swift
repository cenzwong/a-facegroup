import Foundation
import MediaIntelligence

public struct Person: Codable { public let id: String; public let faceCount: Int; public let photoCount: Int; public let paths: [String] }
public struct ScanResult: Codable { public var processed = 0; public var skipped = 0; public var failures: [String] = []; public var noFaces = 0 }
public struct Identification: Codable { public let entityID: String?; public let matched: Bool }
public final class FaceService {
    private let analyzer: FaceGroupAnalyzer
    private let manifestURL: URL
    private var manifest: Manifest
    private let lock: LibraryLock
    public init(directory: URL) throws {
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
        lock = try LibraryLock(directory.appendingPathComponent("library.lock"))
        manifestURL = directory.appendingPathComponent("manifest.json")
        manifest = try Manifest.load(manifestURL)
        let analyzerURL = directory.appendingPathComponent("analyzer", isDirectory: true)
        try FileManager.default.createDirectory(at: analyzerURL, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
        analyzer = try FaceGroupAnalyzer(workingDirectory: analyzerURL)
    }
    private func update() async throws {
        switch await analyzer.state {
        case .stale: try await analyzer.update()
        case .updating: throw Failure("Analyzer is already updating; try again later")
        case .ready: break
        @unknown default: throw Failure("Unknown analyzer state")
        }
    }
    public func scan(_ root: URL, force: Bool) async throws -> ScanResult {
        let root = canonical(root); let urls = try discover(root); var result = ScanResult()
        if !manifest.scanRoots.contains(root.path) { manifest.scanRoots.append(root.path); try manifest.save(manifestURL) }
        for url in urls {
            let existing = manifest.assets.first { $0.path == url.path }
            do {
                var asset = try metadata(url, id: existing?.id ?? UUID().uuidString)
                if let existing, !existing.isPending, !force, existing.size == asset.size && existing.modified == asset.modified { result.skipped += 1; continue }
                // Persist the identifier before ingestion so interrupted runs retry the same asset.
                if let index = manifest.assets.firstIndex(where: { $0.id == asset.id }) { manifest.assets[index].pending = true }
                else { var pending = asset; pending.pending = true; manifest.assets.append(pending) }
                try manifest.save(manifestURL)
                let input = MediaIntelligenceImageAsset(id: .init(asset.id), kind: .url(url))
                // Give each ingestion operation its own task lifetime so framework
                // image buffers can be released before processing the next asset.
                let count = try await Task { [analyzer, input] in
                    var count: Int?
                    for try await (_, faces) in try await analyzer.insertOrUpdateAssets([input]) { count = faces.count }
                    guard let count else { throw Failure("Analyzer returned no result") }
                    return count
                }.value
                asset.faceCount = count
                if let index = manifest.assets.firstIndex(where: { $0.id == asset.id }) { manifest.assets[index] = asset }
                try manifest.save(manifestURL); result.processed += 1
                if asset.faceCount == 0 { result.noFaces += 1 }
            } catch { result.failures.append("\(url.path): \(error.localizedDescription)") }
        }
        try await update(); return result
    }
    public func people() async throws -> [Person] {
        try await update(); let paths = Dictionary(uniqueKeysWithValues: manifest.assets.filter { !$0.isPending }.map { ($0.id, $0.path) }); let knownIDs = Set(manifest.assets.map(\.id)); var people: [Person] = []
        for try await (id, faces) in analyzer.allFacesByEntityID {
            guard faces.allSatisfy({ knownIDs.contains($0.assetID.rawValue) }) else { throw Failure("Analyzer contains assets missing from manifest") }
            let completeFaces = faces.filter { paths[$0.assetID.rawValue] != nil }
            let assetIDs = Set(completeFaces.map { $0.assetID.rawValue }); let mapped = assetIDs.compactMap { paths[$0] }.sorted()
            if !completeFaces.isEmpty { people.append(Person(id: id.rawValue, faceCount: completeFaces.count, photoCount: mapped.count, paths: mapped)) }
        }
        return people.sorted { $0.id < $1.id }
    }
    public func identify(_ url: URL) async throws -> [Identification] {
        let path = canonical(url); _ = try metadata(path, id: "identify")
        var results: [Identification] = []; var received = false
        let input = MediaIntelligenceImageAsset(id: .init(UUID().uuidString), kind: .url(path))
        for try await (_, faces) in try await analyzer.identifyFaces(in: [input]) { received = true; results += faces.map { Identification(entityID: $0.entityID?.rawValue, matched: $0.entityID != nil) } }
        guard received else { throw Failure("Analyzer returned no result") }; return results
    }
    public func planExport(_ destination: URL) async throws -> [ExportItem] {
        guard !isWithin(destination, manifestURL.deletingLastPathComponent()), !isWithin(manifestURL.deletingLastPathComponent(), destination) else { throw Failure("Export destination overlaps library storage") }
        let people = try await people(); var groups: [String: [String]] = [:]
        // Encode native IDs as hex to make arbitrary identifiers safe as folder names.
        for person in people { let folder = "Person_" + person.id.utf8.map { String(format: "%02x", $0) }.joined(); groups[folder] = person.paths }
        groups["No_Faces"] = manifest.assets.filter { !$0.isPending && $0.faceCount == 0 }.map(\.path)
        let exportedPaths = Set(groups.values.flatMap { $0 })
        try validateExportSources(manifest.assets.filter { exportedPaths.contains($0.path) })
        return try exportPlan(destination: destination, groups: groups, scanRoots: manifest.scanRoots.map { URL(fileURLWithPath: $0) })
    }
}
