import XCTest

final class HatInRingUITests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    func testTabsSearchDetailAndPersistedPicks() throws {
        let app = XCUIApplication()
        app.launchArguments = ["-ui-testing-reset", "-ui-testing-skip-intro"]
        app.launch()

        XCTAssertTrue(app.staticTexts["The Field"].waitForExistence(timeout: 6))
        XCTAssertTrue(app.staticTexts["UPDATED"].waitForExistence(timeout: 3))

        app.buttons["tab-wire"].tap()
        XCTAssertTrue(app.staticTexts["The Wire"].waitForExistence(timeout: 3))

        app.buttons["tab-dossiers"].tap()
        XCTAssertTrue(app.staticTexts["Dossiers"].waitForExistence(timeout: 3))

        app.buttons["tab-search"].tap()
        let searchField = app.textFields["Search names, offices, signals..."]
        XCTAssertTrue(searchField.waitForExistence(timeout: 3))
        XCTAssertTrue(app.staticTexts["Search the field"].waitForExistence(timeout: 3))
        let newsomSuggestion = app.buttons["suggestion-chip-newsom"]
        XCTAssertTrue(newsomSuggestion.waitForExistence(timeout: 3))
        newsomSuggestion.tap()

        let newsomRow = app.buttons["candidate-row-newsom"]
        XCTAssertTrue(newsomRow.waitForExistence(timeout: 3))
        newsomRow.tap()

        XCTAssertTrue(app.staticTexts["WHY IT'S ON THE RADAR"].waitForExistence(timeout: 3))
        XCTAssertTrue(app.staticTexts["Momentum ledger"].exists)

        let followButton = app.buttons["Follow Gavin Newsom"]
        XCTAssertTrue(followButton.waitForExistence(timeout: 3))
        followButton.tap()
        XCTAssertTrue(app.buttons["Unfollow Gavin Newsom"].waitForExistence(timeout: 3))

        app.terminate()
        app.launchArguments = ["-ui-testing-skip-intro"]
        app.launch()

        let restoredSearchField = app.textFields["Search names, offices, signals..."]
        XCTAssertTrue(restoredSearchField.waitForExistence(timeout: 6))
        app.buttons["tab-picks"].tap()
        XCTAssertTrue(app.staticTexts["My Picks"].waitForExistence(timeout: 3))
        XCTAssertTrue(app.buttons["candidate-row-newsom"].waitForExistence(timeout: 3))
    }

    func testIntroReviewAndSettingsSurfaces() throws {
        let app = XCUIApplication()
        app.launchArguments = ["-ui-testing-reset"]
        app.launch()

        XCTAssertTrue(app.staticTexts["Track the 2028 field from one native radar surface."].waitForExistence(timeout: 6))
        app.buttons["intro-start-field"].tap()
        XCTAssertTrue(app.staticTexts["The Field"].waitForExistence(timeout: 3))

        app.buttons["tab-dossiers"].tap()
        XCTAssertTrue(app.staticTexts["Dossiers"].waitForExistence(timeout: 3))
        app.buttons["dossier-mode-review"].tap()
        XCTAssertTrue(app.staticTexts["Review queue"].waitForExistence(timeout: 3))
        let reviewItem = app.buttons["Confirm Gretchen Whitmer"].firstMatch
        XCTAssertTrue(reviewItem.waitForExistence(timeout: 3))
        reviewItem.tap()

        app.buttons["tab-settings"].tap()
        XCTAssertTrue(app.staticTexts["Settings"].waitForExistence(timeout: 3))
        XCTAssertTrue(app.staticTexts["Export review decisions"].waitForExistence(timeout: 3))
    }
}
