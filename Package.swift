// swift-tools-version: 6.0
import PackageDescription
let package = Package(name: "a-facegroup", platforms: [.macOS("27.0")], products: [.executable(name: "a-facegroup", targets: ["AFaceGroupCLI"])], targets: [.target(name: "AFaceGroupCore"), .executableTarget(name: "AFaceGroupCLI", dependencies: ["AFaceGroupCore"]), .testTarget(name: "AFaceGroupCoreTests", dependencies: ["AFaceGroupCore"])])
