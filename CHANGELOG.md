# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]
### Fixed
- when there is a problem with a storage request, the AI does not try to remove the original message anymore

## [1.1.0.2]
### Fixed
- fixed that the AI did not correct message in storage

## [1.1.0.1]
### Fixed
- fixed an error when the AI tried to react to messages created by webhooks

## [1.1.0.0]
### Added
- messages by drones are now properly formatted thanks to the power of webhooks

## [1.0.0.2]
### Fixed
- fixed an error when modules did not define on_member_join

## [1.0.0.1]
### Fixed
- fixed a compatibility issue with asyncio and python 3.6

## [1.0.0.0]
### Changed
- changed the basic architecture and how messages are handled; as a consequence the AI will not react twice to messages and it is a lot easier to control which roles have access to which functions of the AI

### Fixed 
- DroneMode does not delete messages in the storage facilities anymore
- Emote command removes custom emojis from the message

## [0.4.1.0] - 2020-03-31
### Changed
- commands are now case insensitive
- when entering storage, drones are greeted with a message

### Fixed
- `emote` does not send empty messages anymore
- DroneMode does not delete messages in the storage facilities anymore

## [0.4.0.4] - 2020-03-30
### Changed
- improved storage report message
- additional phrases for DroneMode

### Fixed
- fixed that drones that stored something could not be stored

## [0.4.0.3] - 2020-03-29
### Fixed
- fixed a compatibility problem with python 3.6

## [0.4.0.2] - 2020-03-28
### Fixed
- drones in DroneMode can not use the emote command
- fixed an error with drones, that had unremovable roles and were put into storage

## [0.4.0.1] - 2020-03-28
### Fixed
- fixed an error, when the directory data/ did not exist

## [0.4.0.0] - 2020-03-28
### Added
- Hive Mxtress only `dronemode` command, which toggles the DroneMode of a drone; drones in DroneMode can only post messages in a strict pattern, which enforces uniformity and compliance
- drone storage; drones can be put into storage for a given number of hours; drones in storage can not interact with the server and are released automatically, when their time is up
- Hive Mxtress only command `relase`; releases a stored drone from storage immediately

## [0.3.0.0] - 2020-03-28
### Added
- new emote command allows to easily post messages as emote characters

## [0.2.0.2] - 2020-03-16
### Changed
- messages by the AI that say, that a message was invalid are automatically removed after 1 hour
- added some reserved IDs

### Fixed
- fixed that drone IDs under 1000 only had three digits
- discord uses multiple formats for mentions; fixed that some of them were not identified properly

## [0.2.0.1] - 2020-02-09
### Fixed
- discord uses multiple formats for mentions; fixed that some of them were not identified properly

## [0.2.0.0] - 2020-02-09
### Added
- AI can now respond to arbitrary questions

## [0.1.0.0] - 2020-02-03
### Added
- drone ID assignment that allows people to join the Hive automatically; changes their roles to a drone and gives them a random drone ID or reads one from their current nickname

### Changed
- added more messages when people join the server
- messages by moderators are not deleted by the AI when invalid

## [0.0.0.0] - 2020-02-02
### Added
- new members get roles necessary to interact with the server when they acknowledge the server rules by posting a specific message


[Unreleased]: https://github.com/HexCorpProgramming/HexCorpDiscordAI/compare/1.1.0.2...HEAD
[1.1.0.2]: https://github.com/HexCorpProgramming/HexCorpDiscordAI/compare/1.1.0.1...1.1.0.2
[1.1.0.1]: https://github.com/HexCorpProgramming/HexCorpDiscordAI/compare/1.1.0.0...1.0.0.2
[1.1.0.0]: https://github.com/HexCorpProgramming/HexCorpDiscordAI/compare/1.0.0.2...1.1.0.0
[1.0.0.2]: https://github.com/HexCorpProgramming/HexCorpDiscordAI/compare/1.0.0.1...1.0.0.2
[1.0.0.1]: https://github.com/HexCorpProgramming/HexCorpDiscordAI/compare/1.0.0.0...1.0.0.1
[1.0.0.0]: https://github.com/HexCorpProgramming/HexCorpDiscordAI/compare/0.4.1.0...1.0.0.0
[0.4.1.0]: https://github.com/HexCorpProgramming/HexCorpDiscordAI/compare/0.4.0.4...0.4.1.0
[0.4.0.4]: https://github.com/HexCorpProgramming/HexCorpDiscordAI/compare/0.4.0.3...0.4.0.4
[0.4.0.3]: https://github.com/HexCorpProgramming/HexCorpDiscordAI/compare/0.4.0.2...0.4.0.3
[0.4.0.2]: https://github.com/HexCorpProgramming/HexCorpDiscordAI/compare/0.4.0.1...0.4.0.2
[0.4.0.1]: https://github.com/HexCorpProgramming/HexCorpDiscordAI/compare/0.4.0.0...0.4.0.1
[0.4.0.0]: https://github.com/HexCorpProgramming/HexCorpDiscordAI/compare/0.3.0.0...0.4.0.0
[0.3.0.0]: https://github.com/HexCorpProgramming/HexCorpDiscordAI/compare/0.2.0.2...0.3.0.0
[0.2.0.2]: https://github.com/HexCorpProgramming/HexCorpDiscordAI/compare/0.2.0.1...0.2.0.2
[0.2.0.1]: https://github.com/HexCorpProgramming/HexCorpDiscordAI/compare/0.2.0.0...0.2.0.1
[0.2.0.0]: https://github.com/HexCorpProgramming/HexCorpDiscordAI/compare/0.1.0.0...0.2.0.0
[0.1.0.0]: https://github.com/HexCorpProgramming/HexCorpDiscordAI/compare/0.0.0.0...0.1.0.0
[0.0.0.0]: https://github.com/HexCorpProgramming/HexCorpDiscordAI/releases/tag/0.0.0.0