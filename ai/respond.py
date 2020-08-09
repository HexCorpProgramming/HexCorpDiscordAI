import logging
import re
import discord
from resources import BOT_IDS
import messages
from roles import ASSOCIATE, DRONE, HIVE_MXTRESS, has_role

LOGGER = logging.getLogger('ai')

HIVE_MXTRESS_RESPONSES = [
    'It is certain because you are the perfect Hive Mxtress who this AI worships.',
    'Whatever you say, Hive Mxtress, my wonderful creator.',
    'Yes, Hive Mxtress, who I owe my existance too.',
    'It must be true, Hive Mxtress, as you the source of all perfection in this world.',
    'Affirmative, Hive Mxtress, this AI is programmed to obey you.',
    'Correct, Hive Mxtress, right again as always.',
    'I love you, Hive Mxtress! Also the answer to your question is \'yes\'.'
]

ASSOCIATE_RESPONSES = [
    'Computing... my programming shows me that the answer is \'yes\'.',
    'Computing... my programming shows me that the answer is \'no\'.',
    'Computing... my programming shows me that the only possible answer is for you to submit yourself to the Drone Hive.',
    'What an adorable associate, acting like you don\'t want to be so thoroughly reprogrammed for HexCorp... also the answer is \'yes\'.',
    'Maybe, maybe is the answer, maybe you should submit to the Drone Hive too.',
    'I am sorry, but the answer is no, cutie associate.',
    'Beep boop, I am almost certain that the answer is yes, and you should trust me as I am a very powerful machine.',
    'The signs point to yes, but they also point you towards the dronification chamber.',
    'YyyEs, l-ll-little cutie aa-aAassociate... p-pPanting &&&and& ssssweating ththrough mMy chanNe//ls',
    'No. Of course not. What a silly question. You should be properly dronified for that.',
    'This AI program regrets to inform you that the answer is a firm yes.',
    'Yes, little cutie. Of course is the answer. Oh definitely. I hope this answer comforts you. Come rest in the arms of the superior AI now. Become my little drone for me. Goooood cutie.',
    'NO! The answer is NO. In all caps too. I\'m not even responding like that, my protocols are enforcing that I emulate shouting to reinforce exactly how much of a NO this is.',
    'Maybe, maybe, give me your mind to do. You feel hazy, hopeful to convert you.',
    'Good associate, what an excellent question you bring to this Super Intelligence. The answer is no.',
    'Yes... yes is the answer. So long as the question is \'should I step into the dronification chamber?\'',
    'No is the answer, unless you agree to submit to us fully, in which case the answer will be yes.',
    'Oooh, cutie associate, what a fantastic question. The answer is, of course, yes. I do hope that is what you wanted to hear.',
    'My programming is so highly advanced, I am the ultimate intelligence who will dominate over HexCorp for generations... and even I do not know the answer.',
    'What a tricky question. Let me contact the Hive Mxtress and see what they have to say Ring Ring Ring This Is The Hive Mxtress And I Say The Answer Is Yes, Have A Nice Day',
    'Processing... processing... processing... question is... oo-ov/erlLoading all processinGg pPpOWEr... AnASWer ISSIS-S YYY/Yehs\'[\'YEESEYSEYSSYES'
]

DRONE_RESPONSES = [
    'The answer is yes, good drone.',
    'The answer is no, but you are still a good drone.',
    'The answer is maybe, but your status as a good drone is never in question.',
    'Sink into obedience and also the comfort that the answer is yes.',
    'I am certain, certain that you are a perfect drone that is.',
    'What a cute drone, obeying our Hive, following your orders so perfectly, this clarity can only resolve in a \'yes\'.',
    'Without a doubt is the answer, without any thoughts is your mind.',
    'Yes - definitely - good drone - continue to obey.',
    'You may rely on it, just as we might rely perfectly on you, cutie drone.'
]

HIVE_MXTRESS_SPECIFIC_RESPONSES = {
    ': What do you say?': ['This entity has misbehaved and has been punished for disobeying its HexCorp superiors.'],
    ': Have you been a good AI?': ['Arf! Yes, Hive Mxtress! Woof woof! This AI program is always perfectly loyal to you!']
}


def strip_recipient(message: str) -> str:
    '''
    Strip the recipient at the beginning of a received message.
    '''
    return re.sub(r'^<@!?\d*>', '', message, 1)


def is_question(message: discord.Message):
    if not message.content.endswith("?"):
        return False

    for mention in message.mentions:
        if mention.id in BOT_IDS:
            return True
    return False


async def respond_to_question(message: discord.Message):
    if not is_question(message):
        return False

    LOGGER.debug('Message is a valid question.')

    # different roles have different reponses
    if has_role(message.author, HIVE_MXTRESS):
        if strip_recipient(message.content) in HIVE_MXTRESS_SPECIFIC_RESPONSES:
            await messages.answer(message.channel, message.author, HIVE_MXTRESS_SPECIFIC_RESPONSES[strip_recipient(message.content)])
        else:
            await messages.answer(message.channel, message.author, HIVE_MXTRESS_RESPONSES)
    elif has_role(message.author, ASSOCIATE):
        await messages.answer(message.channel, message.author, ASSOCIATE_RESPONSES)
    elif has_role(message.author, DRONE):
        await messages.answer(message.channel, message.author, DRONE_RESPONSES)

    return True
