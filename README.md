# <img src='https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/vial.svg' card_color='#40DBB0' width='50' height='50' style='vertical-align:bottom'/> Skill Testing
Internal utterance testing tool

## About
### "read all utterances"
Enter a list of phrases in Skill settings to verify which Skill and intent handler is triggered. Phrase list should be in format:
> phrase one, phrase two, phrase three

Alternatively provide a csv of phrases at: `~/.mycroft/skills/SkillTesting/utterances.csv`

If a phrase contains a comma it must be surrounded with quotation marks:
> phrase one, "phrase, two", phrase three

Additional options include:
- test_identifier - title of the test for your benefit eg 'weather phrases' - default timestamp of test comppletion time.
- delay - the period in seconds between each phrase - default 30

Results will be uploaded to termbin.com in csv format and the link will be emailed to you. A csv file of the results will also be saved on the device at: `~/.mycroft/skills/SkillTesting/reading-output/{test_identifier}.csv`. Note that when creating the filename, characters not in [a-z, A-Z, 0-9, [.\_-]] will be removed eg "weather phrases" will become "weatherphrases.csv". This file can be used to generate integration tests for all phrases.

## Intents being developed - WIP do not use.
### "generate integration tests"
Provide a valid csv or select a previously generated file. An integration test will be created for each phrase within the test folder of that Skill.

To provide your own csv copy the file to: `~/.mycroft/skills/SkillTesting/integration-tests.csv`

### "run integration tests"
Trigger a run of all Skills integration tests on the device. Intended to be run after generating additional tests using the command above.

### "remove generated tests"
Remove all tests generated using this Skill.

If a test is unable to be removed, Mycroft will notify you, and a list of remaining tests will be logged to `skills.log`


## Examples
* "read all utterances"
* "generate integration tests"
* "run integration tests"
* "remove generated tests"

## Credits
krisgesling (@krisgesling)

## Category
**Configuration**

## Tags
#testing
