# Change Log

All notable changes to this project will be documented here.

## [2.0.0] - 2019-10-14
### Changed
- When requesting a single resource using the dictionary way, only a single
  object will be returned instead of a list with a single object.

## [1.0.1] - 2019-10-14
### Fixed
- Correctly return entities when a single one is requested using a resource id
  reflecting changes in HelpScout's API responses.

## [1.0.0] - 2019-09-18
### Changed
- HelpScoutEndpointRequester now returns subentities for methods named other
  than http methods like get / post / put / delete / etc.
- HelpScoutEndpointRequester can now be accessed as a dictionary to request
  specific resources or specific resources sub endpoints (like a conversation's
  tags).
- The client's *hit* method has been renamed to *hit_* and *hit* nows nexts the
  generator.

## [0.2.3] - 2019-07-16
### Fixed
- Setting attributes to HelpScout objects adds them to the attributes list.

## [0.2.2] - 2019-07-12
### Fixed
- Send json data actually as json.

## [0.2.1] - 2019-07-08
### Fixed
- Object creation when requesting a single object.
- Hit an endpoint with a resource_id and url parameters.

## [0.2.0] - 2019-07-01
### Added
- Pickle compatible objects
### Fixed
- Pagination next link format.
- Python 2 compatibility.

## [0.1.0] - 2019-06-28
### Added
- Client to query Help Scout's v2 API.
