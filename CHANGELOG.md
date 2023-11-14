# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]
### Added
- pyproject.toml for packaging
- "home" setting on settings.json. This lets define the execution home and meets the requirements to be able to work with Postfix.
- Added exception handling for writing permissions.
- Windows support
- A path to an email file can be provided as an optional argument that will override stdin

### Changed
- settings_file is now a mandatory argument. We cannot rely on "settings.json" to be inside the home directory if we define that inside the settings itself, it's a chicken vs egg problem.
- Changed relative imports to be absolute, so planckProxy.py can be invoked as a python command too.

### Fixed
- Updated some outdated information in the README
- Added fallback system in case management or keys.db are not present
- Fixed colored output
- Fixed handling multiple "to" recipients

### Removed
- Removed most of the commands of the CLI. Since settings.json is required is less confusing just haveing everything there
- Removed the DEBUG parameter. Log level is managed with the -l parameter.

## [v3.0.0] - 17-5-23
### Added
- Planck Proxy initial release
- Planck core 3 support
- Pytest automated testing for key features
- Added this changelog
