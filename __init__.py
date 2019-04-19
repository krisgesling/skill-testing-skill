from mycroft import MycroftSkill, intent_file_handler
from mycroft.messagebus.message import Message
from os.path import join, exists
from time import sleep

class SkillTesting(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        # self.data_file = '/'.join([self.file_system.path, 'phrases.txt'])
        self.data_file = '/home/pi/.mycroft/skills/SkillTesting/phrases.txt'

    @intent_file_handler('testing.skill.intent')
    def handle_testing_skill(self, message):
        self.speak_dialog('testing.start')
        # Load phrases
        f = open(self.data_file, 'r')
        phrases = f.readlines()
        # Loop over each emitting message

        for phrase in phrases:
            self.speak_dialog('testing.phrase', {'phrase': phrase})
            self.bus.emit(Message("recognizer_loop:utterance",
                              {'utterances': [phrase],
                               'lang': 'en-us'}))
            sleep(10)

def create_skill():
    return SkillTesting()
