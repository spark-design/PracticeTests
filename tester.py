import PySimpleGUI as sg
import random
import json
import os

TESTS_FILE = 'tests.json'

def load_tests():
    if os.path.exists(TESTS_FILE):
        with open(TESTS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_tests(tests):
    with open(TESTS_FILE, 'w') as f:
        json.dump(tests, f)

def create_new_test(tests):
    layout = [
        [sg.Text('Enter new test name:', font=('Helvetica', 12))],
        [sg.Input(key='-TEST_NAME-')],
        [sg.Button('Create', font=('Helvetica', 12)), sg.Button('Cancel', font=('Helvetica', 12))]
    ]
    window = sg.Window('Create New Test', layout, finalize=True)
    
    while True:
        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, 'Cancel'):
            window.close()
            return None
        if event == 'Create':
            test_name = values['-TEST_NAME-']
            if test_name and test_name not in tests:
                tests[test_name] = []
                save_tests(tests)
                window.close()
                return test_name
            else:
                sg.popup('Invalid test name or test already exists.', font=('Helvetica', 12))

def add_questions(current_test, tests):
    add_question_layout = [
        [sg.Text('Paste your questions in JSON format (one or more):', font=('Helvetica', 12))],
        [sg.Multiline(size=(60, 20), key='-JSON-')],
        [sg.Button('Add', font=('Helvetica', 12)), sg.Button('Cancel', font=('Helvetica', 12))]
    ]
    add_window = sg.Window('Add Question(s)', add_question_layout, finalize=True)
    
    while True:
        add_event, add_values = add_window.read()
        if add_event in (sg.WINDOW_CLOSED, 'Cancel'):
            break
        if add_event == 'Add':
            try:
                new_questions = json.loads(add_values['-JSON-'])
                if not isinstance(new_questions, list):
                    new_questions = [new_questions]
                
                valid_questions = []
                for question in new_questions:
                    if all(key in question for key in ('question', 'options', 'answer')) and \
                       isinstance(question['options'], list) and \
                       isinstance(question['answer'], int) and \
                       0 <= question['answer'] < len(question['options']):
                        valid_questions.append(question)
                    else:
                        sg.popup(f'Invalid question format: {question["question"]}', font=('Helvetica', 12))
                
                tests[current_test].extend(valid_questions)
                save_tests(tests)
                sg.popup(f'{len(valid_questions)} question(s) added successfully!', font=('Helvetica', 12))
                break
            except json.JSONDecodeError:
                sg.popup('Invalid JSON format. Please check your input.', font=('Helvetica', 12))
    
    add_window.close()

def review_missed_questions(missed_questions):
    layout = [
        [sg.Text('Missed Questions Review', font=('Helvetica', 16))],
        [sg.Text('', size=(60, 4), key='-QUESTION-', font=('Helvetica', 12))],
        [sg.Text('', size=(60, 2), key='-ANSWER-', font=('Helvetica', 12), text_color='green')],
        [sg.Button('Next', font=('Helvetica', 12)), sg.Button('Close', font=('Helvetica', 12))]
    ]
    window = sg.Window('Missed Questions Review', layout, finalize=True)
    
    question_index = 0
    
    def update_review_question():
        if question_index < len(missed_questions):
            q = missed_questions[question_index]
            window['-QUESTION-'].update(f"Question {question_index + 1}/{len(missed_questions)}:\n\n{q['question']}\n\nOptions:\n" + 
                                        "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(q['options'])]))
            window['-ANSWER-'].update(f"Correct Answer: {q['options'][q['answer']]}")
        else:
            window['-QUESTION-'].update("Review completed!")
            window['-ANSWER-'].update("")
            window['Next'].update(visible=False)
    
    update_review_question()
    
    while True:
        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, 'Close'):
            break
        if event == 'Next':
            question_index += 1
            update_review_question()
    
    window.close()

def run_quiz():
    sg.theme('DefaultNoMoreNagging')

    tests = load_tests()
    current_test = None

    def create_main_layout():
        test_names = list(tests.keys()) + ['Create New Test']
        return [
            [sg.Text('Select a test:', font=('Helvetica', 12)), 
             sg.Combo(test_names, key='-TEST_SELECT-', font=('Helvetica', 12), enable_events=True, readonly=True)],
            [sg.Text('', size=(60, 4), key='-QUESTION-', font=('Helvetica', 12))],
            [sg.Radio('', 'RADIO1', key='-RADIO0-', font=('Helvetica', 10))],
            [sg.Radio('', 'RADIO1', key='-RADIO1-', font=('Helvetica', 10))],
            [sg.Radio('', 'RADIO1', key='-RADIO2-', font=('Helvetica', 10))],
            [sg.Radio('', 'RADIO1', key='-RADIO3-', font=('Helvetica', 10))],
            [sg.Button('Submit', font=('Helvetica', 12)), 
             sg.Button('Delete Question', font=('Helvetica', 12)),
             sg.Button('Add Question(s)', font=('Helvetica', 12)), 
             sg.Button('Exit', font=('Helvetica', 12))]
        ]

    window = sg.Window('AWS Data Analytics Quiz', create_main_layout(), size=(600, 400), finalize=True)

    score = 0
    question_index = 0
    missed_questions = []

    def update_question():
        if not current_test or question_index >= len(tests[current_test]):
            window['-QUESTION-'].update("No questions available or quiz completed!")
            for i in range(4):
                window[f'-RADIO{i}-'].update(text="", visible=False)
            window['Submit'].update(visible=False)
            window['Delete Question'].update(visible=False)
            return

        q = tests[current_test][question_index]
        window['-QUESTION-'].update(f"Question {question_index + 1}/{len(tests[current_test])}:\n\n{q['question']}")
        for i, option in enumerate(q['options']):
            window[f'-RADIO{i}-'].update(text=option, value=False, visible=True)
        window['Submit'].update(visible=True)
        window['Delete Question'].update(visible=True)

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED or event == 'Exit':
            break

        if event == '-TEST_SELECT-':
            selected = values['-TEST_SELECT-']
            if selected == 'Create New Test':
                new_test = create_new_test(tests)
                if new_test:
                    current_test = new_test
                    window['-TEST_SELECT-'].update(values=list(tests.keys()) + ['Create New Test'], value=current_test)
            else:
                current_test = selected
            question_index = 0
            score = 0
            missed_questions = []
            update_question()

        if event == 'Submit' and current_test:
            if question_index < len(tests[current_test]):
                user_answer = next((i for i in range(4) if values[f'-RADIO{i}-']), None)
                if user_answer is not None:
                    correct_answer = tests[current_test][question_index]['answer']

                    if user_answer == correct_answer:
                        score += 1
                        sg.popup('Correct!', font=('Helvetica', 12))
                    else:
                        sg.popup(f'Incorrect. The correct answer was:\n{tests[current_test][question_index]["options"][correct_answer]}', font=('Helvetica', 12))
                        missed_questions.append(tests[current_test][question_index])

                    question_index += 1
                    update_question()
                else:
                    sg.popup('Please select an answer.', font=('Helvetica', 12))

            if question_index >= len(tests[current_test]):
                sg.popup(f'Quiz completed! Your score: {score}/{len(tests[current_test])}', font=('Helvetica', 12))
                if missed_questions:
                    if sg.popup_yes_no('Would you like to review missed questions?', font=('Helvetica', 12)) == 'Yes':
                        review_missed_questions(missed_questions)
                question_index = 0
                score = 0
                missed_questions = []
                update_question()

        if event == 'Delete Question' and current_test:
            if sg.popup_yes_no('Are you sure you want to delete this question?', font=('Helvetica', 12)) == 'Yes':
                del tests[current_test][question_index]
                save_tests(tests)
                if question_index >= len(tests[current_test]):
                    question_index = max(0, len(tests[current_test]) - 1)
                update_question()

        if event == 'Add Question(s)' and current_test:
            add_questions(current_test, tests)
            update_question()

    window.close()

if __name__ == '__main__':
    run_quiz()