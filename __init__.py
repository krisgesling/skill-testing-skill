from mycroft import MycroftSkill, intent_file_handler


class SkillTesting(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('testing.skill.intent')
    def handle_testing_skill(self, message):
        self.speak_dialog('testing.skill')


def create_skill():
    return SkillTesting()

