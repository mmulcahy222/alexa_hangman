import os, sys
import urllib2
import random

def lambda_handler(event, context):
    try:
        #FORCED TO HAVE PROGRAM FLOW with Try & Catch BECAUSE OF A GLITCH IN AMAZON ECHO DEVICE vs Alexa Service Simulator
        try:
            response_session_attributes = event["session"]["attributes"]
        except:
            response_session_attributes = {'debug':'problem with session variables'}

        state = get_session_value(event,'state','menu')
        intent = get_intent(event)
        #return build_ssml_response(intent, 1, response_session_attributes)
        print intent

        bodyparts = ["Gallows","Body","Right Arm","Left Arm","Right Leg","Left Leg"]
        dict_of_bodyparts = {i+1:c for i,c in enumerate(bodyparts[::-1])}
        number_descriptors = {1:'first',2:'second',3:'third',4:'fourth',5:'fifth',6:'sixth',7:'seventh',8:'eighth',9:'ninth',10:'tenth',11:'eleventh',12:'twelveth'}
        
        if state == 'game_over': 
            if intent == "PlayAgainIntent":
                choose_play_again_yn = str(get_slot_value(event,'play_again'))
                if choose_play_again_yn == 'yes':
                    #fall-through
                    state = 'menu'
                    response_session_attributes['state'] = 'menu'
                elif choose_play_again_yn == 'no':
                    return build_ssml_response('Thank you for playing Hang Guy', 1,response_session_attributes)
                else:
                    return build_ssml_response('Do you want to play again?', 0,response_session_attributes)
            else:
                return build_ssml_response('Do you want to play again?', 0,response_session_attributes)

        if state == 'menu':    
            if intent == 'ChooseLevelIntent':
                #change this eventually
                chosen_level = str(get_slot_value(event,'level')).lower()
                if chosen_level not in ['easy','medium','hard']:
                    return build_ssml_response("Please choose a level between easy, medium or hard", 0, response_session_attributes)
                word = get_word(chosen_level)
                response_session_attributes['word'] = word
                response_session_attributes['state'] = 'guessing'
                response_session_attributes['puzzle'] = ""
                response_session_attributes['instruction_flag'] = 1
                response_session_attributes['correct'] = ""
                response_session_attributes['tries_left'] = len(bodyparts)
                instructions = 'Your word is %s letters. Start Guessing Letters' % len(word)
                return build_ssml_response(instructions, 0, response_session_attributes)
            else:
                return build_ssml_response("Please choose a level between easy, medium or hard", 0, response_session_attributes)
        elif state == 'guessing':
            if intent == "ChooseLetterIntent":
                chosen_letter = str(get_slot_value(event,'chosen_letter'))[0].lower()
                word = str(get_session_value(event,'word'))
                debug_text = "%s %s" % (chosen_letter, word)
                word_length = len(word)
                tries_left = int(get_session_value(event,'tries_left'))
                tries_left -= 1
                if tries_left <= 0:
                    response_session_attributes['state'] = 'game_over'
                    return build_ssml_response("You lost. The correct word was %s . Would you like to play again?" % word, 0,response_session_attributes)
                elif chosen_letter in word:   
                    correct = str(get_session_value(event,'correct'))
                    correct += chosen_letter
                    correct_position = 0
                    correct_count = 0
                    puzzle = ''
                    response_letter_placement = ''
                    for i in word:
                        correct_position += 1
                        if i in correct:
                            puzzle += i
                        else:
                            puzzle += "_"
                        if i == chosen_letter:
                            response_letter_placement += " %s is the %s letter, " % (i,number_descriptors[correct_position])
                            if correct_position == len(word):
                                response_letter_placement += '<break time="200ms"/> %s is the last letter. ' % (i)
                            correct_count += 1
                    times = "once" if correct_count == 1 else "%s times" % correct_count
                    response = "%s shows up %s. " % (chosen_letter,times) + response_letter_placement
                    #ONLY GIVE INSTRUCTIONS ON FIRST TRY
                    instruction_flag = int(get_session_value(event,'instruction_flag'))
                    if instruction_flag == 1:
                        response += ' Say, What Do I Have, to hear your progress. Put <break time="40ms"/>Is<break time="10ms"/>It<break time="50ms"/>before your answer'
                        response_session_attributes['instruction_flag'] = 0
                    #CORRECT IF ALL LETTERS ARE SOLVED
                    if puzzle == word:
                        response_session_attributes['state'] = 'game_over'
                        return build_ssml_response('Congratulations. You win! The word was %s. Do you want to play again' % word, 0,response_session_attributes)
                    response_session_attributes['correct'] = correct
                    response_session_attributes['puzzle'] = puzzle

                    return build_ssml_response(response, 0,response_session_attributes, exception=debug_text)
                elif chosen_letter not in word:
                    response = "Sorry, no <say-as interpret-as='spell-out'>%s</say-as>. drawing the %s." % (chosen_letter, dict_of_bodyparts[tries_left])
                    response_session_attributes['tries_left'] = tries_left
                    return build_ssml_response(response, 0,response_session_attributes, exception=debug_text)
                else:
                    return build_ssml_response("You said  <say-as interpret-as='spell-out'>%s</say-as>. If you want to solve, say I'd like to solve" % chosen_letter, 0,response_session_attributes,exception=word)
            if intent == "RemindIntent":
                puzzle = str(get_session_value(event,'puzzle')).lower()
                word = str(get_session_value(event,'word'))
                response = 'You have a %s letter word<break time="500ms"/>' % len(word)  + '<break time="300ms"/>'.join(['blank' if i=='_' else i for i in list(puzzle)])
                return build_ssml_response(response, 0,response_session_attributes)
            if intent == "SolveIntent":
                solve = str(get_slot_value(event,'solve'))
                word = str(get_session_value(event,'word'))
                if solve == word:
                    response_session_attributes['state'] = 'game_over'
                    return build_ssml_response('Congratulations. You win! Do you want to play again', 0,response_session_attributes)
                else:
                    response_session_attributes['state'] = 'guessing'
                    return build_ssml_response('%s is not the answer. Please choose more letters or solve again.' % solve, 0,response_session_attributes)                
            if intent == "AMAZON.CancelIntent" or intent == "AMAZON.StopIntent":
                return build_ssml_response('Thank you for using Hang Guy. See you next time!', 1)
            else:
                return build_ssml_response('Please guess more letters or solve the puzzle. Say, is it, before the answer', 0,response_session_attributes)


    except:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        exception_text = str(exc_type) + ' ' + str(fname) + ' ' + str(exc_tb.tb_lineno)
        response_session_attributes['exception'] = exception_text
        return build_ssml_response("I did not understand you. Can you please say it again?",0,response_session_attributes,exception=exception_text)

#####
# PLEASE REPLACE URL IF YOU ARE CHANGING IT!!! WORDS MUST BE SEPARATED IN NEW LINES
#####
def get_word(level):
    results = urllib2.urlopen('http://pastebin.com/raw/baKjRnDu').read()
    list_of_results = results.split("\n")
    length_of_results = len(list_of_results)
    dict_of_lengths = {'easy':[3,4],'medium':[5,6],'hard':[7,8,9,10,11,12]}
    while True:
        list_index = random.randrange(0,length_of_results-1)
        word = list_of_results[list_index].strip()
        list_index += 1
        if list_index == length_of_results - 1:
            list_index = 0 
        if len(word) in dict_of_lengths[level]:
            break
    return word



def get_intent(event):
    if event["request"]["type"] == "LaunchRequest":
        return "LaunchRequest"
    elif event["request"]["type"] == "IntentRequest":
        return event["request"]["intent"]["name"]
    else:
        return False

def get_session_value(event,key,default=False):
    try:
        value = event.get('session').get('attributes').get(key,default)
        return value
    except TypeError:
        return default
    except:
        return default

def get_slot_value(event,key,default=False):
    try:
        attribute = event.get('request').get('intent').get('slots').get(key).get('value')
        return attribute
    except TypeError:
        return default
    except:
        return default

def build_ssml_response(speech_output, should_end_session, session_attributes = {}, **kwargs):
    response = {
        "version": "1.0",
        "sessionAttributes": session_attributes,
        "response": {
            "outputSpeech": {
                "type": "SSML",
                "ssml":"<speak>" + str(speech_output)[:7999] + "</speak>"
            },
            "reprompt": {
                "outputSpeech": {
                    "type": "SSML",
                    "ssml": "<speak>" + str(speech_output)[:7999] + "</speak>"
                }
            },
            "shouldEndSession": should_end_session
        }
    }
    #if problem playing on amazon echo device
    try:
        if kwargs['exception'] is not False:
            response['response']['card'] = {"type": "Simple", "title": 'title', "content": kwargs['exception']}
    #except is GOOD in this case & normal
    except:
        pass
    return response
