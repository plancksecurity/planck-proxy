# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]
### Added

### Changed

### Fixed


### Removed

## [v3.1.0] - 22-11-23
### Added
- pyproject.toml for packaging
- "home" setting on settings.json. This lets define the execution home and meets the requirements to be able to work with Postfix.
- Added exception handling for writing permissions.
- Windows support
- A path to an email file can be provided as an optional argument that will override stdin
- "-l", "--loglevel" argument can be used to specify the loglevel of the output. This gets rid of the "DEBUG" argument.
- "export_dir" on settings.json to specify the absolute path to a folder where the unencrypted emails and session logs will be stored.
- "export_log_level" on settings.json to specify the log level of exported files.


### Changed
- settings_file is now a mandatory argument. We cannot rely on "settings.json" to be inside the home directory if we define that inside the settings itself, it's a chicken vs egg problem.
- Changed relative imports to be absolute, so planckProxy.py can be invoked as a python command too.
- Timestamps in folders and logs follow RFC3339 and are all in UTC.
- Changed Dockerfile to new github repos.

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
