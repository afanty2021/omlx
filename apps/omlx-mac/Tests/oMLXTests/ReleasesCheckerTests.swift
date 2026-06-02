import XCTest
@testable import oMLX

final class ReleasesCheckerTests: XCTestCase {

    func testCompareVersionsOrdersPrereleaseSuffixes() {
        XCTAssertEqual(
            ReleasesChecker.compareVersions("0.4.0rc2", "0.4.0rc1"),
            .orderedDescending
        )
        XCTAssertEqual(
            ReleasesChecker.compareVersions("0.4.0", "0.4.0rc2"),
            .orderedDescending
        )
        XCTAssertEqual(
            ReleasesChecker.compareVersions("0.4.0rc1", "0.4.0.dev1"),
            .orderedDescending
        )
    }

    func testStableChannelExcludesPrereleases() {
        let selected = ReleasesChecker.selectLatest(
            [
                release("v0.4.0rc2"),
                release("v0.3.12"),
            ],
            channel: .stable
        )

        XCTAssertEqual(selected?.tagName, "v0.3.12")
    }

    func testReleaseCandidateChannelIncludesRCButExcludesDev() {
        let selected = ReleasesChecker.selectLatest(
            [
                release("v0.4.1.dev1"),
                release("v0.4.0rc2"),
                release("v0.4.0rc1"),
            ],
            channel: .releaseCandidate
        )

        XCTAssertEqual(selected?.tagName, "v0.4.0rc2")
    }

    func testDevChannelIncludesDev() {
        let selected = ReleasesChecker.selectLatest(
            [
                release("v0.4.1.dev1"),
                release("v0.4.0rc2"),
                release("v0.4.0"),
            ],
            channel: .dev
        )

        XCTAssertEqual(selected?.tagName, "v0.4.1.dev1")
    }

    private func release(
        _ tag: String,
        prerelease: Bool = false,
        draft: Bool = false
    ) -> GitHubRelease {
        GitHubRelease(
            tagName: tag,
            name: tag,
            body: nil,
            htmlURL: URL(string: "https://github.com/jundot/omlx/releases/tag/\(tag)")!,
            prerelease: prerelease,
            draft: draft,
            assets: []
        )
    }
}
