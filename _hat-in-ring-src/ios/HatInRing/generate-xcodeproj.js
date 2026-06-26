#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

const appName = "HatInRing";
const bundleID = "com.davehomeassist.hatinring";
const root = __dirname;
const srcDir = path.join(root, appName);
const testDir = path.join(root, `${appName}Tests`);
const uiTestDir = path.join(root, `${appName}UITests`);
const assetsName = "Assets.xcassets";
const assetsDir = path.join(srcDir, assetsName);
const resourceName = "HatInRingData";
const resourceDir = path.join(srcDir, resourceName);

const appFiles = fs.readdirSync(srcDir).filter((file) => file.endsWith(".swift")).sort();
const testFiles = fs.existsSync(testDir)
  ? fs.readdirSync(testDir).filter((file) => file.endsWith(".swift")).sort()
  : [];
const uiTestFiles = fs.existsSync(uiTestDir)
  ? fs.readdirSync(uiTestDir).filter((file) => file.endsWith(".swift")).sort()
  : [];

let counter = 1;
const id = () => (counter++).toString(16).toUpperCase().padStart(24, "0");

const PROJECT = id();
const APP_TARGET = id();
const TEST_TARGET = id();
const UI_TEST_TARGET = id();
const GROUP_ROOT = id();
const GROUP_APP = id();
const GROUP_TESTS = id();
const GROUP_UI_TESTS = id();
const GROUP_PRODUCTS = id();
const PRODUCT_APP = id();
const PRODUCT_TESTS = id();
const PRODUCT_UI_TESTS = id();
const PHASE_APP_SOURCES = id();
const PHASE_APP_FRAMEWORKS = id();
const PHASE_APP_RESOURCES = id();
const PHASE_TEST_SOURCES = id();
const PHASE_TEST_FRAMEWORKS = id();
const PHASE_TEST_RESOURCES = id();
const PHASE_UI_TEST_SOURCES = id();
const PHASE_UI_TEST_FRAMEWORKS = id();
const PHASE_UI_TEST_RESOURCES = id();
const CFGLIST_PROJECT = id();
const CFGLIST_APP = id();
const CFGLIST_TESTS = id();
const CFGLIST_UI_TESTS = id();
const CFG_PROJECT_DEBUG = id();
const CFG_PROJECT_RELEASE = id();
const CFG_APP_DEBUG = id();
const CFG_APP_RELEASE = id();
const CFG_TEST_DEBUG = id();
const CFG_TEST_RELEASE = id();
const CFG_UI_TEST_DEBUG = id();
const CFG_UI_TEST_RELEASE = id();
const ASSETS_REF = id();
const ASSETS_BUILD = id();
const RESOURCE_REF = id();
const RESOURCE_BUILD = id();
const TEST_PROXY = id();
const TEST_DEPENDENCY = id();
const UI_TEST_PROXY = id();
const UI_TEST_DEPENDENCY = id();

const appObjects = appFiles.map((name) => ({ name, ref: id(), build: id() }));
const testObjects = testFiles.map((name) => ({ name, ref: id(), build: id() }));
const uiTestObjects = uiTestFiles.map((name) => ({ name, ref: id(), build: id() }));

const lines = (items) => items.join("\n");

const appBuildFiles = appObjects.map((file) =>
  `\t\t${file.build} /* ${file.name} in Sources */ = {isa = PBXBuildFile; fileRef = ${file.ref} /* ${file.name} */; };`
);
const testBuildFiles = testObjects.map((file) =>
  `\t\t${file.build} /* ${file.name} in Sources */ = {isa = PBXBuildFile; fileRef = ${file.ref} /* ${file.name} */; };`
);
const uiTestBuildFiles = uiTestObjects.map((file) =>
  `\t\t${file.build} /* ${file.name} in Sources */ = {isa = PBXBuildFile; fileRef = ${file.ref} /* ${file.name} */; };`
);

const appFileRefs = appObjects.map((file) =>
  `\t\t${file.ref} /* ${file.name} */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = "${file.name}"; sourceTree = "<group>"; };`
);
const testFileRefs = testObjects.map((file) =>
  `\t\t${file.ref} /* ${file.name} */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = "${file.name}"; sourceTree = "<group>"; };`
);
const uiTestFileRefs = uiTestObjects.map((file) =>
  `\t\t${file.ref} /* ${file.name} */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = "${file.name}"; sourceTree = "<group>"; };`
);

const appGroupChildren = appObjects
  .map((file) => `\t\t\t\t${file.ref} /* ${file.name} */,`)
  .concat(fs.existsSync(assetsDir) ? [`\t\t\t\t${ASSETS_REF} /* ${assetsName} */,`] : [])
  .concat(fs.existsSync(resourceDir) ? [`\t\t\t\t${RESOURCE_REF} /* ${resourceName} */,`] : []);
const testGroupChildren = testObjects.map((file) => `\t\t\t\t${file.ref} /* ${file.name} */,`);
const uiTestGroupChildren = uiTestObjects.map((file) => `\t\t\t\t${file.ref} /* ${file.name} */,`);
const appSourceFiles = appObjects.map((file) => `\t\t\t\t${file.build} /* ${file.name} in Sources */,`);
const testSourceFiles = testObjects.map((file) => `\t\t\t\t${file.build} /* ${file.name} in Sources */,`);
const uiTestSourceFiles = uiTestObjects.map((file) => `\t\t\t\t${file.build} /* ${file.name} in Sources */,`);

const projectDebug = `
\t\t\t\tALWAYS_SEARCH_USER_PATHS = NO;
\t\t\t\tCLANG_ANALYZER_NONNULL = YES;
\t\t\t\tCLANG_ENABLE_MODULES = YES;
\t\t\t\tCLANG_ENABLE_OBJC_ARC = YES;
\t\t\t\tCOPY_PHASE_STRIP = NO;
\t\t\t\tDEBUG_INFORMATION_FORMAT = dwarf;
\t\t\t\tENABLE_STRICT_OBJC_MSGSEND = YES;
\t\t\t\tENABLE_TESTABILITY = YES;
\t\t\t\tGCC_DYNAMIC_NO_PIC = NO;
\t\t\t\tGCC_OPTIMIZATION_LEVEL = 0;
\t\t\t\tGCC_PREPROCESSOR_DEFINITIONS = (
\t\t\t\t\t"DEBUG=1",
\t\t\t\t\t"$(inherited)",
\t\t\t\t);
\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = 17.0;
\t\t\t\tMTL_ENABLE_DEBUG_INFO = INCLUDE_SOURCE;
\t\t\t\tONLY_ACTIVE_ARCH = YES;
\t\t\t\tSDKROOT = iphoneos;
\t\t\t\tSWIFT_ACTIVE_COMPILATION_CONDITIONS = DEBUG;
\t\t\t\tSWIFT_OPTIMIZATION_LEVEL = "-Onone";
\t\t\t\tSWIFT_VERSION = 5.0;`;

const projectRelease = `
\t\t\t\tALWAYS_SEARCH_USER_PATHS = NO;
\t\t\t\tCLANG_ANALYZER_NONNULL = YES;
\t\t\t\tCLANG_ENABLE_MODULES = YES;
\t\t\t\tCLANG_ENABLE_OBJC_ARC = YES;
\t\t\t\tCOPY_PHASE_STRIP = NO;
\t\t\t\tDEBUG_INFORMATION_FORMAT = "dwarf-with-dsym";
\t\t\t\tENABLE_NS_ASSERTIONS = NO;
\t\t\t\tENABLE_STRICT_OBJC_MSGSEND = YES;
\t\t\t\tGCC_OPTIMIZATION_LEVEL = s;
\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = 17.0;
\t\t\t\tMTL_ENABLE_DEBUG_INFO = NO;
\t\t\t\tSDKROOT = iphoneos;
\t\t\t\tSWIFT_COMPILATION_MODE = wholemodule;
\t\t\t\tSWIFT_OPTIMIZATION_LEVEL = "-O";
\t\t\t\tSWIFT_VERSION = 5.0;
\t\t\t\tVALIDATE_PRODUCT = YES;`;

const appSettings = `
\t\t\t\tASSETCATALOG_COMPILER_APPICON_NAME = AppIcon;
\t\t\t\tASSETCATALOG_COMPILER_GENERATE_ASSET_SYMBOLS = NO;
\t\t\t\tCODE_SIGN_STYLE = Automatic;
\t\t\t\tCURRENT_PROJECT_VERSION = 1;
\t\t\t\tENABLE_DEBUG_DYLIB = NO;
\t\t\t\tENABLE_PREVIEWS = NO;
\t\t\t\tGENERATE_INFOPLIST_FILE = NO;
\t\t\t\tINFOPLIST_FILE = ${appName}/Info.plist;
\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = 17.0;
\t\t\t\tLD_RUNPATH_SEARCH_PATHS = (
\t\t\t\t\t"$(inherited)",
\t\t\t\t\t"@executable_path/Frameworks",
\t\t\t\t);
\t\t\t\tMARKETING_VERSION = 1.0;
\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = ${bundleID};
\t\t\t\tPRODUCT_NAME = "$(TARGET_NAME)";
\t\t\t\tSWIFT_EMIT_LOC_STRINGS = YES;
\t\t\t\tSWIFT_VERSION = 5.0;
\t\t\t\tTARGETED_DEVICE_FAMILY = "1,2";`;

const testSettings = `
\t\t\t\tBUNDLE_LOADER = "$(TEST_HOST)";
\t\t\t\tCODE_SIGN_STYLE = Automatic;
\t\t\t\tCURRENT_PROJECT_VERSION = 1;
\t\t\t\tGENERATE_INFOPLIST_FILE = YES;
\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = 17.0;
\t\t\t\tLD_RUNPATH_SEARCH_PATHS = (
\t\t\t\t\t"$(inherited)",
\t\t\t\t\t"@executable_path/Frameworks",
\t\t\t\t\t"@loader_path/Frameworks",
\t\t\t\t\t"$(DEVELOPER_DIR)/Platforms/iPhoneSimulator.platform/Developer/usr/lib",
\t\t\t\t\t"$(DEVELOPER_DIR)/Platforms/iPhoneOS.platform/Developer/usr/lib",
\t\t\t\t);
\t\t\t\tMARKETING_VERSION = 1.0;
\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = ${bundleID}.Tests;
\t\t\t\tPRODUCT_NAME = "$(TARGET_NAME)";
\t\t\t\tSWIFT_VERSION = 5.0;
\t\t\t\tTARGETED_DEVICE_FAMILY = "1,2";
\t\t\t\tTEST_HOST = "$(BUILT_PRODUCTS_DIR)/${appName}.app/$(BUNDLE_EXECUTABLE_FOLDER_PATH)/${appName}";`;

const uiTestSettings = `
\t\t\t\tCODE_SIGN_STYLE = Automatic;
\t\t\t\tCURRENT_PROJECT_VERSION = 1;
\t\t\t\tGENERATE_INFOPLIST_FILE = YES;
\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = 17.0;
\t\t\t\tLD_RUNPATH_SEARCH_PATHS = (
\t\t\t\t\t"$(inherited)",
\t\t\t\t\t"@executable_path/Frameworks",
\t\t\t\t\t"@loader_path/Frameworks",
\t\t\t\t\t"$(DEVELOPER_DIR)/Platforms/iPhoneSimulator.platform/Developer/usr/lib",
\t\t\t\t\t"$(DEVELOPER_DIR)/Platforms/iPhoneOS.platform/Developer/usr/lib",
\t\t\t\t);
\t\t\t\tMARKETING_VERSION = 1.0;
\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = ${bundleID}.UITests;
\t\t\t\tPRODUCT_NAME = "$(TARGET_NAME)";
\t\t\t\tSWIFT_VERSION = 5.0;
\t\t\t\tTARGETED_DEVICE_FAMILY = "1,2";
\t\t\t\tTEST_TARGET_NAME = ${appName};`;

const assetsBuild = fs.existsSync(assetsDir)
  ? `\t\t${ASSETS_BUILD} /* ${assetsName} in Resources */ = {isa = PBXBuildFile; fileRef = ${ASSETS_REF} /* ${assetsName} */; };`
  : "";
const assetsRef = fs.existsSync(assetsDir)
  ? `\t\t${ASSETS_REF} /* ${assetsName} */ = {isa = PBXFileReference; lastKnownFileType = folder.assetcatalog; path = ${assetsName}; sourceTree = "<group>"; };`
  : "";
const assetsFile = fs.existsSync(assetsDir)
  ? `\t\t\t\t${ASSETS_BUILD} /* ${assetsName} in Resources */,`
  : "";
const resourceBuild = fs.existsSync(resourceDir)
  ? `\t\t${RESOURCE_BUILD} /* ${resourceName} in Resources */ = {isa = PBXBuildFile; fileRef = ${RESOURCE_REF} /* ${resourceName} */; };`
  : "";
const resourceRef = fs.existsSync(resourceDir)
  ? `\t\t${RESOURCE_REF} /* ${resourceName} */ = {isa = PBXFileReference; lastKnownFileType = folder; path = ${resourceName}; sourceTree = "<group>"; };`
  : "";
const resourceFile = fs.existsSync(resourceDir)
  ? `\t\t\t\t${RESOURCE_BUILD} /* ${resourceName} in Resources */,`
  : "";

const pbx = `// !$*UTF8*$!
{
\tarchiveVersion = 1;
\tclasses = {
\t};
\tobjectVersion = 56;
\tobjects = {

/* Begin PBXBuildFile section */
${lines(appBuildFiles)}
${lines(testBuildFiles)}
${lines(uiTestBuildFiles)}
${assetsBuild}
${resourceBuild}
/* End PBXBuildFile section */

/* Begin PBXContainerItemProxy section */
\t\t${TEST_PROXY} /* PBXContainerItemProxy */ = {
\t\t\tisa = PBXContainerItemProxy;
\t\t\tcontainerPortal = ${PROJECT} /* Project object */;
\t\t\tproxyType = 1;
\t\t\tremoteGlobalIDString = ${APP_TARGET};
\t\t\tremoteInfo = ${appName};
\t\t};
\t\t${UI_TEST_PROXY} /* PBXContainerItemProxy */ = {
\t\t\tisa = PBXContainerItemProxy;
\t\t\tcontainerPortal = ${PROJECT} /* Project object */;
\t\t\tproxyType = 1;
\t\t\tremoteGlobalIDString = ${APP_TARGET};
\t\t\tremoteInfo = ${appName};
\t\t};
/* End PBXContainerItemProxy section */

/* Begin PBXFileReference section */
\t\t${PRODUCT_APP} /* ${appName}.app */ = {isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = ${appName}.app; sourceTree = BUILT_PRODUCTS_DIR; };
\t\t${PRODUCT_TESTS} /* ${appName}Tests.xctest */ = {isa = PBXFileReference; explicitFileType = wrapper.cfbundle; includeInIndex = 0; path = ${appName}Tests.xctest; sourceTree = BUILT_PRODUCTS_DIR; };
\t\t${PRODUCT_UI_TESTS} /* ${appName}UITests.xctest */ = {isa = PBXFileReference; explicitFileType = wrapper.cfbundle; includeInIndex = 0; path = ${appName}UITests.xctest; sourceTree = BUILT_PRODUCTS_DIR; };
${assetsRef}
${lines(appFileRefs)}
${lines(testFileRefs)}
${lines(uiTestFileRefs)}
${resourceRef}
/* End PBXFileReference section */

/* Begin PBXFrameworksBuildPhase section */
\t\t${PHASE_APP_FRAMEWORKS} /* Frameworks */ = {
\t\t\tisa = PBXFrameworksBuildPhase;
\t\t\tbuildActionMask = 2147483647;
\t\t\tfiles = (
\t\t\t);
\t\t\trunOnlyForDeploymentPostprocessing = 0;
\t\t};
\t\t${PHASE_TEST_FRAMEWORKS} /* Frameworks */ = {
\t\t\tisa = PBXFrameworksBuildPhase;
\t\t\tbuildActionMask = 2147483647;
\t\t\tfiles = (
\t\t\t);
\t\t\trunOnlyForDeploymentPostprocessing = 0;
\t\t};
\t\t${PHASE_UI_TEST_FRAMEWORKS} /* Frameworks */ = {
\t\t\tisa = PBXFrameworksBuildPhase;
\t\t\tbuildActionMask = 2147483647;
\t\t\tfiles = (
\t\t\t);
\t\t\trunOnlyForDeploymentPostprocessing = 0;
\t\t};
/* End PBXFrameworksBuildPhase section */

/* Begin PBXGroup section */
\t\t${GROUP_ROOT} = {
\t\t\tisa = PBXGroup;
\t\t\tchildren = (
\t\t\t\t${GROUP_APP} /* ${appName} */,
\t\t\t\t${GROUP_TESTS} /* ${appName}Tests */,
\t\t\t\t${GROUP_UI_TESTS} /* ${appName}UITests */,
\t\t\t\t${GROUP_PRODUCTS} /* Products */,
\t\t\t);
\t\t\tsourceTree = "<group>";
\t\t};
\t\t${GROUP_APP} /* ${appName} */ = {
\t\t\tisa = PBXGroup;
\t\t\tchildren = (
${lines(appGroupChildren)}
\t\t\t);
\t\t\tpath = ${appName};
\t\t\tsourceTree = "<group>";
\t\t};
\t\t${GROUP_TESTS} /* ${appName}Tests */ = {
\t\t\tisa = PBXGroup;
\t\t\tchildren = (
${lines(testGroupChildren)}
\t\t\t);
\t\t\tpath = ${appName}Tests;
\t\t\tsourceTree = "<group>";
\t\t};
\t\t${GROUP_UI_TESTS} /* ${appName}UITests */ = {
\t\t\tisa = PBXGroup;
\t\t\tchildren = (
${lines(uiTestGroupChildren)}
\t\t\t);
\t\t\tpath = ${appName}UITests;
\t\t\tsourceTree = "<group>";
\t\t};
\t\t${GROUP_PRODUCTS} /* Products */ = {
\t\t\tisa = PBXGroup;
\t\t\tchildren = (
\t\t\t\t${PRODUCT_APP} /* ${appName}.app */,
\t\t\t\t${PRODUCT_TESTS} /* ${appName}Tests.xctest */,
\t\t\t\t${PRODUCT_UI_TESTS} /* ${appName}UITests.xctest */,
\t\t\t);
\t\t\tname = Products;
\t\t\tsourceTree = "<group>";
\t\t};
/* End PBXGroup section */

/* Begin PBXNativeTarget section */
\t\t${APP_TARGET} /* ${appName} */ = {
\t\t\tisa = PBXNativeTarget;
\t\t\tbuildConfigurationList = ${CFGLIST_APP} /* Build configuration list for PBXNativeTarget "${appName}" */;
\t\t\tbuildPhases = (
\t\t\t\t${PHASE_APP_SOURCES} /* Sources */,
\t\t\t\t${PHASE_APP_FRAMEWORKS} /* Frameworks */,
\t\t\t\t${PHASE_APP_RESOURCES} /* Resources */,
\t\t\t);
\t\t\tbuildRules = (
\t\t\t);
\t\t\tdependencies = (
\t\t\t);
\t\t\tname = ${appName};
\t\t\tproductName = ${appName};
\t\t\tproductReference = ${PRODUCT_APP} /* ${appName}.app */;
\t\t\tproductType = "com.apple.product-type.application";
\t\t};
\t\t${TEST_TARGET} /* ${appName}Tests */ = {
\t\t\tisa = PBXNativeTarget;
\t\t\tbuildConfigurationList = ${CFGLIST_TESTS} /* Build configuration list for PBXNativeTarget "${appName}Tests" */;
\t\t\tbuildPhases = (
\t\t\t\t${PHASE_TEST_SOURCES} /* Sources */,
\t\t\t\t${PHASE_TEST_FRAMEWORKS} /* Frameworks */,
\t\t\t\t${PHASE_TEST_RESOURCES} /* Resources */,
\t\t\t);
\t\t\tbuildRules = (
\t\t\t);
\t\t\tdependencies = (
\t\t\t\t${TEST_DEPENDENCY} /* PBXTargetDependency */,
\t\t\t);
\t\t\tname = ${appName}Tests;
\t\t\tproductName = ${appName}Tests;
\t\t\tproductReference = ${PRODUCT_TESTS} /* ${appName}Tests.xctest */;
\t\t\tproductType = "com.apple.product-type.bundle.unit-test";
\t\t};
\t\t${UI_TEST_TARGET} /* ${appName}UITests */ = {
\t\t\tisa = PBXNativeTarget;
\t\t\tbuildConfigurationList = ${CFGLIST_UI_TESTS} /* Build configuration list for PBXNativeTarget "${appName}UITests" */;
\t\t\tbuildPhases = (
\t\t\t\t${PHASE_UI_TEST_SOURCES} /* Sources */,
\t\t\t\t${PHASE_UI_TEST_FRAMEWORKS} /* Frameworks */,
\t\t\t\t${PHASE_UI_TEST_RESOURCES} /* Resources */,
\t\t\t);
\t\t\tbuildRules = (
\t\t\t);
\t\t\tdependencies = (
\t\t\t\t${UI_TEST_DEPENDENCY} /* PBXTargetDependency */,
\t\t\t);
\t\t\tname = ${appName}UITests;
\t\t\tproductName = ${appName}UITests;
\t\t\tproductReference = ${PRODUCT_UI_TESTS} /* ${appName}UITests.xctest */;
\t\t\tproductType = "com.apple.product-type.bundle.ui-testing";
\t\t};
/* End PBXNativeTarget section */

/* Begin PBXProject section */
\t\t${PROJECT} /* Project object */ = {
\t\t\tisa = PBXProject;
\t\t\tattributes = {
\t\t\t\tBuildIndependentTargetsInParallel = 1;
\t\t\t\tLastSwiftUpdateCheck = 2600;
\t\t\t\tLastUpgradeCheck = 2600;
\t\t\t\tTargetAttributes = {
\t\t\t\t\t${APP_TARGET} = {
\t\t\t\t\t\tCreatedOnToolsVersion = 26.0;
\t\t\t\t\t};
\t\t\t\t\t${TEST_TARGET} = {
\t\t\t\t\t\tCreatedOnToolsVersion = 26.0;
\t\t\t\t\t\tTestTargetID = ${APP_TARGET};
\t\t\t\t\t};
\t\t\t\t\t${UI_TEST_TARGET} = {
\t\t\t\t\t\tCreatedOnToolsVersion = 26.0;
\t\t\t\t\t\tTestTargetID = ${APP_TARGET};
\t\t\t\t\t};
\t\t\t\t};
\t\t\t};
\t\t\tbuildConfigurationList = ${CFGLIST_PROJECT} /* Build configuration list for PBXProject "${appName}" */;
\t\t\tcompatibilityVersion = "Xcode 14.0";
\t\t\tdevelopmentRegion = en;
\t\t\thasScannedForEncodings = 0;
\t\t\tknownRegions = (
\t\t\t\ten,
\t\t\t\tBase,
\t\t\t);
\t\t\tmainGroup = ${GROUP_ROOT};
\t\t\tproductRefGroup = ${GROUP_PRODUCTS} /* Products */;
\t\t\tprojectDirPath = "";
\t\t\tprojectRoot = "";
\t\t\ttargets = (
\t\t\t\t${APP_TARGET} /* ${appName} */,
\t\t\t\t${TEST_TARGET} /* ${appName}Tests */,
\t\t\t\t${UI_TEST_TARGET} /* ${appName}UITests */,
\t\t\t);
\t\t};
/* End PBXProject section */

/* Begin PBXResourcesBuildPhase section */
\t\t${PHASE_APP_RESOURCES} /* Resources */ = {
\t\t\tisa = PBXResourcesBuildPhase;
\t\t\tbuildActionMask = 2147483647;
\t\t\tfiles = (
${assetsFile}
${resourceFile}
\t\t\t);
\t\t\trunOnlyForDeploymentPostprocessing = 0;
\t\t};
\t\t${PHASE_TEST_RESOURCES} /* Resources */ = {
\t\t\tisa = PBXResourcesBuildPhase;
\t\t\tbuildActionMask = 2147483647;
\t\t\tfiles = (
\t\t\t);
\t\t\trunOnlyForDeploymentPostprocessing = 0;
\t\t};
\t\t${PHASE_UI_TEST_RESOURCES} /* Resources */ = {
\t\t\tisa = PBXResourcesBuildPhase;
\t\t\tbuildActionMask = 2147483647;
\t\t\tfiles = (
\t\t\t);
\t\t\trunOnlyForDeploymentPostprocessing = 0;
\t\t};
/* End PBXResourcesBuildPhase section */

/* Begin PBXSourcesBuildPhase section */
\t\t${PHASE_APP_SOURCES} /* Sources */ = {
\t\t\tisa = PBXSourcesBuildPhase;
\t\t\tbuildActionMask = 2147483647;
\t\t\tfiles = (
${lines(appSourceFiles)}
\t\t\t);
\t\t\trunOnlyForDeploymentPostprocessing = 0;
\t\t};
\t\t${PHASE_TEST_SOURCES} /* Sources */ = {
\t\t\tisa = PBXSourcesBuildPhase;
\t\t\tbuildActionMask = 2147483647;
\t\t\tfiles = (
${lines(testSourceFiles)}
\t\t\t);
\t\t\trunOnlyForDeploymentPostprocessing = 0;
\t\t};
\t\t${PHASE_UI_TEST_SOURCES} /* Sources */ = {
\t\t\tisa = PBXSourcesBuildPhase;
\t\t\tbuildActionMask = 2147483647;
\t\t\tfiles = (
${lines(uiTestSourceFiles)}
\t\t\t);
\t\t\trunOnlyForDeploymentPostprocessing = 0;
\t\t};
/* End PBXSourcesBuildPhase section */

/* Begin PBXTargetDependency section */
\t\t${TEST_DEPENDENCY} /* PBXTargetDependency */ = {
\t\t\tisa = PBXTargetDependency;
\t\t\ttarget = ${APP_TARGET} /* ${appName} */;
\t\t\ttargetProxy = ${TEST_PROXY} /* PBXContainerItemProxy */;
\t\t};
\t\t${UI_TEST_DEPENDENCY} /* PBXTargetDependency */ = {
\t\t\tisa = PBXTargetDependency;
\t\t\ttarget = ${APP_TARGET} /* ${appName} */;
\t\t\ttargetProxy = ${UI_TEST_PROXY} /* PBXContainerItemProxy */;
\t\t};
/* End PBXTargetDependency section */

/* Begin XCBuildConfiguration section */
\t\t${CFG_PROJECT_DEBUG} /* Debug */ = {
\t\t\tisa = XCBuildConfiguration;
\t\t\tbuildSettings = {${projectDebug}
\t\t\t};
\t\t\tname = Debug;
\t\t};
\t\t${CFG_PROJECT_RELEASE} /* Release */ = {
\t\t\tisa = XCBuildConfiguration;
\t\t\tbuildSettings = {${projectRelease}
\t\t\t};
\t\t\tname = Release;
\t\t};
\t\t${CFG_APP_DEBUG} /* Debug */ = {
\t\t\tisa = XCBuildConfiguration;
\t\t\tbuildSettings = {${appSettings}
\t\t\t};
\t\t\tname = Debug;
\t\t};
\t\t${CFG_APP_RELEASE} /* Release */ = {
\t\t\tisa = XCBuildConfiguration;
\t\t\tbuildSettings = {${appSettings}
\t\t\t};
\t\t\tname = Release;
\t\t};
\t\t${CFG_TEST_DEBUG} /* Debug */ = {
\t\t\tisa = XCBuildConfiguration;
\t\t\tbuildSettings = {${testSettings}
\t\t\t};
\t\t\tname = Debug;
\t\t};
\t\t${CFG_TEST_RELEASE} /* Release */ = {
\t\t\tisa = XCBuildConfiguration;
\t\t\tbuildSettings = {${testSettings}
\t\t\t};
\t\t\tname = Release;
\t\t};
\t\t${CFG_UI_TEST_DEBUG} /* Debug */ = {
\t\t\tisa = XCBuildConfiguration;
\t\t\tbuildSettings = {${uiTestSettings}
\t\t\t};
\t\t\tname = Debug;
\t\t};
\t\t${CFG_UI_TEST_RELEASE} /* Release */ = {
\t\t\tisa = XCBuildConfiguration;
\t\t\tbuildSettings = {${uiTestSettings}
\t\t\t};
\t\t\tname = Release;
\t\t};
/* End XCBuildConfiguration section */

/* Begin XCConfigurationList section */
\t\t${CFGLIST_PROJECT} /* Build configuration list for PBXProject "${appName}" */ = {
\t\t\tisa = XCConfigurationList;
\t\t\tbuildConfigurations = (
\t\t\t\t${CFG_PROJECT_DEBUG} /* Debug */,
\t\t\t\t${CFG_PROJECT_RELEASE} /* Release */,
\t\t\t);
\t\t\tdefaultConfigurationIsVisible = 0;
\t\t\tdefaultConfigurationName = Release;
\t\t};
\t\t${CFGLIST_APP} /* Build configuration list for PBXNativeTarget "${appName}" */ = {
\t\t\tisa = XCConfigurationList;
\t\t\tbuildConfigurations = (
\t\t\t\t${CFG_APP_DEBUG} /* Debug */,
\t\t\t\t${CFG_APP_RELEASE} /* Release */,
\t\t\t);
\t\t\tdefaultConfigurationIsVisible = 0;
\t\t\tdefaultConfigurationName = Release;
\t\t};
\t\t${CFGLIST_TESTS} /* Build configuration list for PBXNativeTarget "${appName}Tests" */ = {
\t\t\tisa = XCConfigurationList;
\t\t\tbuildConfigurations = (
\t\t\t\t${CFG_TEST_DEBUG} /* Debug */,
\t\t\t\t${CFG_TEST_RELEASE} /* Release */,
\t\t\t);
\t\t\tdefaultConfigurationIsVisible = 0;
\t\t\tdefaultConfigurationName = Release;
\t\t};
\t\t${CFGLIST_UI_TESTS} /* Build configuration list for PBXNativeTarget "${appName}UITests" */ = {
\t\t\tisa = XCConfigurationList;
\t\t\tbuildConfigurations = (
\t\t\t\t${CFG_UI_TEST_DEBUG} /* Debug */,
\t\t\t\t${CFG_UI_TEST_RELEASE} /* Release */,
\t\t\t);
\t\t\tdefaultConfigurationIsVisible = 0;
\t\t\tdefaultConfigurationName = Release;
\t\t};
/* End XCConfigurationList section */
\t};
\trootObject = ${PROJECT} /* Project object */;
}
`;

const projectDir = path.join(root, `${appName}.xcodeproj`);
fs.mkdirSync(projectDir, { recursive: true });
fs.writeFileSync(path.join(projectDir, "project.pbxproj"), pbx);

const appBuildableRef =
  `<BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="${APP_TARGET}" BuildableName="${appName}.app" BlueprintName="${appName}" ReferencedContainer="container:${appName}.xcodeproj"></BuildableReference>`;
const testBuildableRef =
  `<BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="${TEST_TARGET}" BuildableName="${appName}Tests.xctest" BlueprintName="${appName}Tests" ReferencedContainer="container:${appName}.xcodeproj"></BuildableReference>`;
const uiTestBuildableRef =
  `<BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="${UI_TEST_TARGET}" BuildableName="${appName}UITests.xctest" BlueprintName="${appName}UITests" ReferencedContainer="container:${appName}.xcodeproj"></BuildableReference>`;

const scheme = `<?xml version="1.0" encoding="UTF-8"?>
<Scheme LastUpgradeVersion="2600" version="1.7">
   <BuildAction parallelizeBuildables="YES" buildImplicitDependencies="YES">
      <BuildActionEntries>
         <BuildActionEntry buildForTesting="YES" buildForRunning="YES" buildForProfiling="YES" buildForArchiving="YES" buildForAnalyzing="YES">
            ${appBuildableRef}
         </BuildActionEntry>
         <BuildActionEntry buildForTesting="YES" buildForRunning="NO" buildForProfiling="NO" buildForArchiving="NO" buildForAnalyzing="YES">
            ${testBuildableRef}
         </BuildActionEntry>
         <BuildActionEntry buildForTesting="YES" buildForRunning="NO" buildForProfiling="NO" buildForArchiving="NO" buildForAnalyzing="YES">
            ${uiTestBuildableRef}
         </BuildActionEntry>
      </BuildActionEntries>
   </BuildAction>
   <TestAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.DebuggerFoundation.Launcher.LLDB" shouldUseLaunchSchemeArgsEnv="YES">
      <Testables>
         <TestableReference skipped="NO" parallelizable="YES">
            ${testBuildableRef}
         </TestableReference>
         <TestableReference skipped="NO" parallelizable="NO">
            ${uiTestBuildableRef}
         </TestableReference>
      </Testables>
      <MacroExpansion>
         ${appBuildableRef}
      </MacroExpansion>
   </TestAction>
   <LaunchAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.DebuggerFoundation.Launcher.LLDB" launchStyle="0" useCustomWorkingDirectory="NO" ignoresPersistentStateOnLaunch="NO" debugDocumentVersioning="YES" debugServiceExtension="internal" allowLocationSimulation="YES">
      <BuildableProductRunnable runnableDebuggingMode="0">
         ${appBuildableRef}
      </BuildableProductRunnable>
   </LaunchAction>
   <ProfileAction buildConfiguration="Release" shouldUseLaunchSchemeArgsEnv="YES" savedToolIdentifier="" useCustomWorkingDirectory="NO" debugDocumentVersioning="YES">
      <BuildableProductRunnable runnableDebuggingMode="0">
         ${appBuildableRef}
      </BuildableProductRunnable>
   </ProfileAction>
   <AnalyzeAction buildConfiguration="Debug">
   </AnalyzeAction>
   <ArchiveAction buildConfiguration="Release" revealArchiveInOrganizer="YES">
   </ArchiveAction>
</Scheme>
`;

const schemeDir = path.join(projectDir, "xcshareddata", "xcschemes");
fs.mkdirSync(schemeDir, { recursive: true });
fs.writeFileSync(path.join(schemeDir, `${appName}.xcscheme`), scheme);

console.log(`Wrote ${appName}.xcodeproj with ${appFiles.length} app Swift files, ${testFiles.length} test Swift files, and ${uiTestFiles.length} UI test Swift files.`);
