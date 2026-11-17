import XCTest
@testable import AFaceGroupCore

final class CoreTests: XCTestCase {
    func temporary() throws -> URL { let u = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString); try FileManager.default.createDirectory(at: u, withIntermediateDirectories: true); addTeardownBlock { try? FileManager.default.removeItem(at: u) }; return u }
    func testDiscoverySkipsSymlinksAndFiltersExtensions() throws {
        let root = try temporary(); let fm = FileManager.default
        try fm.createDirectory(at: root.appendingPathComponent("nested"), withIntermediateDirectories: true)
        try Data().write(to: root.appendingPathComponent("nested/a.JPG")); try Data().write(to: root.appendingPathComponent("x.txt"))
        try fm.createSymbolicLink(at: root.appendingPathComponent("cycle"), withDestinationURL: root)
        XCTAssertEqual(try discover(root).map(\.lastPathComponent), ["a.JPG"])
    }
    func testManifestRoundTrip() throws {
        let root = try temporary(); let path = root.appendingPathComponent("manifest.json"); var manifest = Manifest()
        manifest.assets = [Asset(id: "id", path: "/a", size: 12, modified: 3, faceCount: 1)]; try manifest.save(path)
        XCTAssertEqual(try Manifest.load(path).assets.first?.id, "id")
    }
    func testExportDeduplicatesAndAvoidsCollisions() throws {
        let root = try temporary(); let dest = root.appendingPathComponent("out")
        let plan = try exportPlan(destination: dest, groups: ["one": ["/a/x.jpg", "/b/x.jpg", "/a/x.jpg"], "two": ["/a/x.jpg"]], scanRoots: [])
        XCTAssertEqual(plan.count, 3); XCTAssertEqual(Set(plan.map(\.destination)).count, 3)
        XCTAssertFalse(FileManager.default.fileExists(atPath: dest.path))
    }
    func testRejectsOverlappingRootsAndSymlinkEscape() throws {
        let root = try temporary(); XCTAssertThrowsError(try exportPlan(destination: root.appendingPathComponent("out"), groups: [:], scanRoots: [root]))
        let dest = root.appendingPathComponent("out"); try FileManager.default.createDirectory(at: dest, withIntermediateDirectories: true)
        try FileManager.default.createSymbolicLink(at: dest.appendingPathComponent("one"), withDestinationURL: root)
        XCTAssertThrowsError(try exportPlan(destination: dest, groups: ["one": ["/a.jpg"]], scanRoots: []))
    }
    func testCopyDoesNotOverwrite() throws {
        let root = try temporary(); let source = root.appendingPathComponent("source.jpg"); try Data("original".utf8).write(to: source)
        let dest = root.appendingPathComponent("out"); let plan = try exportPlan(destination: dest, groups: ["one": [source.path]], scanRoots: [])
        try applyExport(plan, mode: "copy"); XCTAssertThrowsError(try applyExport(plan, mode: "copy")); XCTAssertEqual(try Data(contentsOf: source), Data("original".utf8))
    }
    func testLockRejectsConcurrentLibraryAccess() throws {
        let root = try temporary(); let path = root.appendingPathComponent("lock")
        let lock = try LibraryLock(path)
        XCTAssertThrowsError(try LibraryLock(path))
        withExtendedLifetime(lock) {}
    }
    func testExistingExportIsPreservedAndRenamed() throws {
        let root = try temporary(); let group = root.appendingPathComponent("out/person")
        try FileManager.default.createDirectory(at: group, withIntermediateDirectories: true)
        let existing = group.appendingPathComponent("x.jpg"); try Data("existing".utf8).write(to: existing)
        let plan = try exportPlan(destination: root.appendingPathComponent("out"), groups: ["person": ["/a/x.jpg"]], scanRoots: [])
        XCTAssertEqual(URL(fileURLWithPath: plan[0].destination).lastPathComponent, "x-2.jpg")
        XCTAssertEqual(try Data(contentsOf: existing), Data("existing".utf8))
    }

}
