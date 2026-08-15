import Darwin
import XCTest
@testable import oMLX

final class UpdateInstallerTests: XCTestCase {
    private var temporaryDirectory: URL!

    override func setUpWithError() throws {
        temporaryDirectory = FileManager.default.temporaryDirectory
            .appendingPathComponent("omlx update $HOME \"quoted\" \(UUID().uuidString)")
        try FileManager.default.createDirectory(
            at: temporaryDirectory,
            withIntermediateDirectories: true
        )
    }

    override func tearDownWithError() throws {
        try? FileManager.default.removeItem(at: temporaryDirectory)
    }

    func testWorkerRequestPreservesPathsWithoutShellParsing() throws {
        let live = temporaryDirectory.appendingPathComponent("oMLX.app")
        let staged = temporaryDirectory.appendingPathComponent(
            UpdateInstaller.stagedAppName
        )

        let request = try XCTUnwrap(UpdateInstaller.workerRequest(from: [
            "/Applications/oMLX.app/Contents/MacOS/oMLX",
            UpdateInstaller.workerModeArgument,
            "1234",
            live.path,
            staged.path,
        ]))

        XCTAssertEqual(request.parentPID, 1234)
        XCTAssertEqual(request.liveApp, live.standardizedFileURL)
        XCTAssertEqual(request.stagedApp, staged.standardizedFileURL)
    }

    func testLaunchAgentRunsOnceWithoutKeepAlive() throws {
        let live = temporaryDirectory.appendingPathComponent("oMLX.app")
        let staged = temporaryDirectory.appendingPathComponent(
            UpdateInstaller.stagedAppName
        )
        let executable = live.appendingPathComponent("Contents/MacOS/oMLX")

        let plist = UpdateInstaller.launchAgentPropertyList(
            label: "app.omlx.updater.test",
            executable: executable,
            parentPID: 1234,
            liveApp: live,
            stagedApp: staged
        )

        XCTAssertEqual(plist["RunAtLoad"] as? Bool, true)
        XCTAssertEqual(plist["KeepAlive"] as? Bool, false)
        XCTAssertEqual(plist["ProgramArguments"] as? [String], [
            executable.path,
            UpdateInstaller.workerModeArgument,
            "1234",
            live.path,
            staged.path,
        ])
    }

    func testAtomicSwapExchangesCompleteBundles() throws {
        let live = try makeBundle(name: "oMLX.app", marker: "old")
        let staged = try makeBundle(
            name: UpdateInstaller.stagedAppName,
            marker: "new"
        )

        try UpdateInstaller.atomicSwap(liveApp: live, stagedApp: staged)

        XCTAssertEqual(try marker(in: live), "new")
        XCTAssertEqual(try marker(in: staged), "old")
    }

    func testAtomicSwapFailureLeavesLiveBundleUntouched() throws {
        let live = try makeBundle(name: "oMLX.app", marker: "old")
        let missingStaged = temporaryDirectory.appendingPathComponent(
            UpdateInstaller.stagedAppName
        )

        XCTAssertThrowsError(
            try UpdateInstaller.atomicSwap(
                liveApp: live,
                stagedApp: missingStaged
            )
        )
        XCTAssertEqual(try marker(in: live), "old")
        XCTAssertFalse(FileManager.default.fileExists(atPath: missingStaged.path))
    }

    func testWaitForProcessExitObservesIndependentProcess() throws {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/sleep")
        process.arguments = ["0.2"]
        try process.run()

        XCTAssertTrue(
            UpdateInstaller.waitForProcessExit(
                process.processIdentifier,
                timeout: 2
            )
        )
    }

    func testLaunchAgentWorkerSmoke() throws {
        let identifier = "app.omlx.updater.smoke.\(UUID().uuidString)"
        let live = try makeLaunchableBundle(
            name: "oMLX.app",
            marker: "old",
            identifier: identifier
        )
        let staged = try makeLaunchableBundle(
            name: UpdateInstaller.stagedAppName,
            marker: "new",
            identifier: identifier
        )
        let jobsDirectory = temporaryDirectory.appendingPathComponent("jobs")
        defer { UpdateInstaller.cleanupLaunchAgents(in: jobsDirectory) }

        let parent = Process()
        parent.executableURL = URL(fileURLWithPath: "/bin/sleep")
        parent.arguments = ["0.3"]
        try parent.run()

        let executable = try XCTUnwrap(Bundle.main.executableURL)
        try UpdateInstaller.submitWorker(
            parentPID: parent.processIdentifier,
            liveApp: live,
            stagedApp: staged,
            executable: executable,
            jobsDirectory: jobsDirectory
        )
        parent.waitUntilExit()

        let deadline = Date().addingTimeInterval(5)
        while Date() < deadline, try marker(in: live) != "new" {
            Thread.sleep(forTimeInterval: 0.1)
        }

        XCTAssertEqual(try marker(in: live), "new")
        XCTAssertEqual(try marker(in: staged), "old")
        Thread.sleep(forTimeInterval: 0.5)
        XCTAssertEqual(try marker(in: live), "new")
        XCTAssertEqual(try marker(in: staged), "old")
    }

    private func makeBundle(name: String, marker: String) throws -> URL {
        let bundle = temporaryDirectory.appendingPathComponent(name)
        try FileManager.default.createDirectory(
            at: bundle,
            withIntermediateDirectories: true
        )
        try Data(marker.utf8).write(to: bundle.appendingPathComponent("marker"))
        return bundle
    }

    private func makeLaunchableBundle(
        name: String,
        marker: String,
        identifier: String
    ) throws -> URL {
        let bundle = temporaryDirectory.appendingPathComponent(name)
        let contents = bundle.appendingPathComponent("Contents")
        let macOS = contents.appendingPathComponent("MacOS")
        try FileManager.default.createDirectory(
            at: macOS,
            withIntermediateDirectories: true
        )
        try FileManager.default.copyItem(
            at: URL(fileURLWithPath: "/usr/bin/true"),
            to: macOS.appendingPathComponent("smoke")
        )
        let info: [String: Any] = [
            "CFBundleExecutable": "smoke",
            "CFBundleIdentifier": identifier,
            "CFBundleName": "oMLX updater smoke",
            "CFBundlePackageType": "APPL",
            "CFBundleShortVersionString": marker == "new" ? "2.0" : "1.0",
            "CFBundleVersion": marker == "new" ? "2" : "1",
            "LSBackgroundOnly": true,
        ]
        let data = try PropertyListSerialization.data(
            fromPropertyList: info,
            format: .binary,
            options: 0
        )
        try data.write(to: contents.appendingPathComponent("Info.plist"))
        try Data(marker.utf8).write(to: bundle.appendingPathComponent("marker"))
        return bundle
    }

    private func marker(in bundle: URL) throws -> String {
        try String(
            contentsOf: bundle.appendingPathComponent("marker"),
            encoding: .utf8
        )
    }
}
