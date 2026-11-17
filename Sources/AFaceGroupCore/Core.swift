import Foundation
import Darwin

public struct Failure: LocalizedError { public let message: String; public init(_ message: String) { self.message = message }; public var errorDescription: String? { message } }
public struct Asset: Codable, Sendable {
    public var id: String; public var path: String; public var size: UInt64; public var modified: Double; public var faceCount: Int
    public var pending: Bool?
    public var isPending: Bool { pending ?? (modified == -1) }
    public init(id: String, path: String, size: UInt64, modified: Double, faceCount: Int = 0) { self.id = id; self.path = path; self.size = size; self.modified = modified; self.faceCount = faceCount; self.pending = false }
}
public struct Manifest: Codable {
    public var assets: [Asset] = []
    public var scanRoots: [String] = []
    public init() {}
    public static func load(_ url: URL) throws -> Manifest {
        guard FileManager.default.fileExists(atPath: url.path) else { return Manifest() }
        return try JSONDecoder().decode(Manifest.self, from: Data(contentsOf: url))
    }
    public func save(_ url: URL) throws { let encoder = JSONEncoder(); encoder.outputFormatting = [.prettyPrinted, .sortedKeys]; try encoder.encode(self).write(to: url, options: .atomic) }
}
public func canonical(_ url: URL) -> URL { url.standardizedFileURL.resolvingSymlinksInPath() }
public func isWithin(_ child: URL, _ parent: URL) -> Bool { let c = canonical(child).path; let p = canonical(parent).path; return c == p || c.hasPrefix(p == "/" ? "/" : p + "/") }
public struct DiscoveryResult {
    public let urls: [URL]
    public let failures: [String]
}
public func discover(_ root: URL) throws -> DiscoveryResult {
    let fm = FileManager.default; var directory: ObjCBool = false
    guard fm.fileExists(atPath: root.path, isDirectory: &directory), directory.boolValue else { throw Failure("Scan path is not a directory: \(root.path)") }
    var urls: [URL] = []; var errors: [String] = []
    guard let enumerator = fm.enumerator(at: root, includingPropertiesForKeys: [.isRegularFileKey, .isSymbolicLinkKey], options: [], errorHandler: { url, error in errors.append("\(url.path): \(error.localizedDescription)"); return true }) else { throw Failure("Cannot enumerate \(root.path)") }
    for case let url as URL in enumerator {
        do {
            let values = try url.resourceValues(forKeys: [.isRegularFileKey, .isSymbolicLinkKey])
            if values.isSymbolicLink == true { continue }
            if values.isRegularFile == true && ["jpg", "jpeg", "png", "heic"].contains(url.pathExtension.lowercased()) { urls.append(canonical(url)) }
        } catch {
            errors.append("\(url.path): \(error.localizedDescription)")
        }
    }
    return DiscoveryResult(urls: Array(Set(urls)).sorted { $0.path < $1.path }, failures: errors)
}
public func metadata(_ url: URL, id: String) throws -> Asset {
    let values = try url.resourceValues(forKeys: [.fileSizeKey, .contentModificationDateKey, .isRegularFileKey])
    guard values.isRegularFile == true, let size = values.fileSize, let date = values.contentModificationDate else { throw Failure("Cannot read file metadata: \(url.path)") }
    return Asset(id: id, path: canonical(url).path, size: UInt64(size), modified: date.timeIntervalSince1970)
}
/// Refuse to export paths whose contents may no longer match the indexed faces.
public func validateExportSources(_ assets: [Asset]) throws {
    for asset in assets {
        let url = URL(fileURLWithPath: asset.path)
        let current: Asset
        do { current = try metadata(url, id: asset.id) }
        catch { throw Failure("Indexed photo is unavailable; rescan or restore it: \(asset.path)") }
        guard current.path == asset.path, current.size == asset.size, current.modified == asset.modified else {
            throw Failure("Indexed photo has changed; rescan before exporting: \(asset.path)")
        }
    }
}
public final class LibraryLock {
    private let fd: Int32
    public init(_ url: URL) throws {
        fd = open(url.path, O_CREAT | O_RDWR, S_IRUSR | S_IWUSR)
        guard fd >= 0 else { throw Failure("Cannot open library lock") }
        guard flock(fd, LOCK_EX | LOCK_NB) == 0 else { close(fd); throw Failure("Library is in use by another process") }
    }
    deinit { flock(fd, LOCK_UN); close(fd) }
}
public struct ExportItem: Codable, Equatable { public let source: String; public let destination: String; public init(source: String, destination: String) { self.source = source; self.destination = destination } }
private func pathOccupied(_ url: URL) throws -> Bool {
    var info = stat()
    if lstat(url.path, &info) == 0 { return true }
    if errno == ENOENT { return false }
    throw Failure("Cannot inspect export destination: \(url.path)")
}
public func exportPlan(destination: URL, groups: [String: [String]], scanRoots: [URL]) throws -> [ExportItem] {
    let dest = canonical(destination)
    for root in scanRoots where isWithin(dest, root) || isWithin(root, dest) { throw Failure("Export destination and source directories must not overlap") }
    var result: [ExportItem] = []; var used = Set<String>()
    for group in groups.keys.sorted() {
        guard !group.isEmpty, group != ".", group != "..", !group.contains("/") else { throw Failure("Unsafe group identifier") }
        let groupURL = dest.appendingPathComponent(group)
        guard isWithin(groupURL, dest), canonical(groupURL).deletingLastPathComponent().path == dest.path else { throw Failure("Unsafe export directory: \(groupURL.path)") }
        for source in Set(groups[group] ?? []).sorted() {
            let url = URL(fileURLWithPath: source); let name = url.lastPathComponent
            var target = dest.appendingPathComponent(group).appendingPathComponent(name)
            var n = 2
            while try used.contains(target.path.lowercased()) || pathOccupied(target) {
                let ext = url.pathExtension; let stem = url.deletingPathExtension().lastPathComponent
                target = dest.appendingPathComponent(group).appendingPathComponent("\(stem)-\(n)" + (ext.isEmpty ? "" : ".\(ext)")); n += 1
            }
            used.insert(target.path.lowercased()); result.append(ExportItem(source: source, destination: target.path))
        }
    }
    return result
}
public func applyExport(_ plan: [ExportItem], mode: String) throws {
    let fm = FileManager.default
    for item in plan {
        let source = URL(fileURLWithPath: item.source); let target = URL(fileURLWithPath: item.destination)
        try fm.createDirectory(at: target.deletingLastPathComponent(), withIntermediateDirectories: true)
        if mode == "copy" { try fm.copyItem(at: source, to: target) }
        else if mode == "symlink" { try fm.createSymbolicLink(at: target, withDestinationURL: source) }
        else { throw Failure("Unknown export mode: \(mode)") }
    }
}
