from __future__ import print_function
import google.auth
import gspread 
import os
import re
import datetime
import pandas as pd
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
# The code on line 4 was taken from this url:
# https://stackoverflow.com/questions/67551298/using-python-to-create-a-new-google-sheet
from gspread_dataframe import set_with_dataframe
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv(dotenv_path="envfile.env")

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
    ]

CREDS = Credentials.from_service_account_file("creds.json")
SCOPED_CREDS = CREDS.with_scopes(SCOPE)
GSPREAD_CLIENT = gspread.authorize(SCOPED_CREDS)
SHEET = GSPREAD_CLIENT.open('UT2 Tracker Spreadsheet')
email_address = os.getenv("EMAIL_ADDRESS")


def type_username():
    """
    Here is where the user will enter
    their username.
    """
    username = input("Type your username here.\n If you're a new user, remember this username so you can access your data again in future. If you've visited us before, we will fetch your existing data!\n")
    return username


def create_new_user_workbook():
    """
    Creates new spreadsheet in Google Sheets.
    """
    # Create new workbook with three worksheets.
    # Workbook will include user's typed username.
    # Three worksheets have titles listed below.
    # Default "Sheet1" worksheet gets deleted.
    # Worksheet list object created to be referred to later when formatting.
    user_workbook = GSPREAD_CLIENT.create(f"{username} UT2 Tracker Spreadsheet")
    worksheet_names = ["Treadmill", "Rowing Ergometer", "Exercise Bike"]
    worksheets = []
    for worksheet_name in worksheet_names:
        worksheet = user_workbook.add_worksheet(title=worksheet_name, rows=1000, cols=3)
        worksheets.append(worksheet)
    user_workbook.del_worksheet(user_workbook.sheet1)
    # Add cell formatting rule to be applied to all worksheets.
    cell_format = {
        "textFormat": {
            "bold": True
        }
    }
    cells_to_format = ['A1', 'B1', 'C1']
    for cell in cells_to_format:
        for worksheet in worksheets:
            worksheet.format(cell, cell_format)
    # Created nested for loops to iterate cell headings
    # across all three of user's worksheets.
    all_worksheet_types = user_workbook.worksheets()
    worksheet_headings = ["Date", "Duration", "Distance"]
    for i, worksheet in enumerate(all_worksheet_types):
        for j in range (3):
            worksheet.update_cell(1, j+1, worksheet_headings[j])
    if email_address:
        user_workbook.share(email_address, perm_type='user', role='writer')
    else:
        print("Email address not found in the environment variables.")


def search_file():
    """Search file in drive location

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    creds = CREDS

    try:
        # create drive api client
        service = build('drive', 'v3', credentials=creds)
        files = []
        page_token = None
        while True:
            # pylint: disable=maybe-no-member
            response = service.files().list(q=f"name='{username} UT2 Tracker Spreadsheet'",
                                            spaces='drive',
                                            fields='nextPageToken,'
                                                   'files(name)',
                                            pageToken=page_token).execute()
            for file in response.get('files', []):
                # Process change
                existing_user_choice()
            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)
            if not files:
                print(f"Thanks for signing up {username}!\n")
                create_new_user_workbook()
                user_workout_choice()
            if page_token is None:
                break
            
    except HttpError as error:
        print(F'An error occurred: {error}')
        files = None

    return files


def user_workout_choice():
    """
    This will allow user to select which workout they want to log
    and write their data to the appropriate worksheet.
    """
    print("What kind of workout would you like to log today?")
    print("1. Treadmill\n2. Rowing Ergometer\n3. Exercise Bike")

    workout_choice = None

    while workout_choice not in ['1', '2', '3']:
        workout_choice = input("Type 1, 2 or 3 to choose one of the above.")
    workout_choice = int(workout_choice)

    if workout_choice == 1:
        print("You've chosen to update your treadmill data.")
        time_data = input_workout_duration_info()
        validate_user_workout_duration_input(time_data)
        distance_data = input_workout_distance_info()
        validate_user_workout_distance_input(distance_data)  
        update_worksheet(time_data, distance_data, "Treadmill")

    elif workout_choice == 2:
        print("You've chosen to update your rowing ergometer data.")
        time_data = input_workout_duration_info()
        validate_user_workout_duration_input(time_data)
        distance_data = input_workout_distance_info()
        validate_user_workout_distance_input(distance_data)
        update_worksheet(time_data, distance_data, "Rowing Ergometer")

    elif workout_choice == 3:
        print("You've chosen to update your exercise bike data.")
        time_data = input_workout_duration_info()
        validate_user_workout_duration_input(time_data)
        distance_data = input_workout_distance_info()
        validate_user_workout_distance_input(distance_data)
        update_worksheet(time_data, distance_data, "Exercise Bike")


def existing_user_choice():
    """
    This will allow an existing user
    to decide if they want to log a new workout
    or get data about their previous workouts.
    """
    print(f"Welcome back {username}! What would you like to do today?")
    print("1. Log a new workout\n2. View the data from previous workouts\n3. View your averge scores from your last three workouts\n")
    user_choice = None

    while user_choice not in ['1', '2', '3',]:
        user_choice = input("Type 1, 2 or 3 to choose one of the above.")
    user_choice = int(user_choice)
    
    if user_choice == 1:
        print("You've chosen to log a new workout.")
        user_workout_choice()

    if user_choice == 2:
        print("You've chosen to view the data from your previous workouts.\n")
        print("Type 1 to view your treadmill workout data.\nType 2 to view your rowing ergometer data.\nType 3 to view your exercise bike data.")
        worksheet = None
        while worksheet not in ['1', '2', '3']:
            worksheet = input("Type 1, 2 or 3 to choose one of the above.")
        worksheet = int(worksheet)
        if worksheet == 1:
            worksheet = "Treadmill"
        elif worksheet == 2:
            worksheet = "Rowing Ergometer"
        elif worksheet == 3:
            worksheet = "Exercise Bike"
        display_all_previous_workout_entries(worksheet)

    if user_choice == 3:
        print("You've chosen to view your averge scores from your last three workouts.")
        print("Type 1 to view your average treadmill workout data.\nType 2 to view your average rowing ergometer data.\nType 3 to view your average exercise bike data.")
        worksheet = None
        while worksheet not in ['1', '2', '3']:
            worksheet = input("Type 1, 2 or 3 to choose one of the above.")
        worksheet = int(worksheet)
        if worksheet == 1:
            worksheet = "Treadmill"
        elif worksheet == 2:
            worksheet = "Rowing Ergometer"
        elif worksheet == 3:
            worksheet = "Exercise Bike"
        calculate_average_workout_scores(worksheet)


def display_all_previous_workout_entries(worksheet):
    """
    This function will allow the user to see their data from 
    past workouts.
    """
    username_sheet = GSPREAD_CLIENT.open(f'{username} UT2 Tracker Spreadsheet')
    workout_type_to_be_displayed = username_sheet.worksheet(worksheet)
    columns = []
    for ind in range(1,4):
        column = workout_type_to_be_displayed.col_values(ind)
        columns.append(column)
    df = pd.DataFrame(columns).transpose()
    df.columns = ["Column 1", "Column 2", "Column 3"]
    print(df)
    return df


def calculate_average_workout_scores(worksheet):
    """
    This function will display the user's average
    workout duration and distance covered for a given
    workout type using the 3 most recent entries.
    """
    username_sheet = GSPREAD_CLIENT.open(f'{username} UT2 Tracker Spreadsheet')
    workout_type_to_be_displayed = username_sheet.worksheet(worksheet)
    duration_column_entries = workout_type_to_be_displayed.col_values(2)
    if len(duration_column_entries) >= 4:
        duration_column_last_three_entries = duration_column_entries[-3:]
        # Convert time values to seconds
        seconds = [datetime.datetime.strptime(t, '%H:%M:%S').time().second + datetime.datetime.strptime(t, '%H:%M:%S').time().minute * 60 + datetime.datetime.strptime(t, '%H:%M:%S').time().hour * 3600 for t in duration_column_last_three_entries]
        # Calculate average of seconds
        avg_seconds = sum(seconds) / len(seconds)
        # Convert average seconds back to hh:mm:ss format
        avg_time = str(datetime.timedelta(seconds=avg_seconds))
        print(f"Your average workout duration for your last three {worksheet} workouts is {avg_time}.")
    elif len(duration_column_entries) < 4 and len(duration_column_entries) > 1:
        print(f"You haven't logged three {worksheet} workouts yet, but here's your existing data anyway!")
        # Convert time values to seconds
        seconds = [datetime.datetime.strptime(t, '%H:%M:%S').time().second + datetime.datetime.strptime(t, '%H:%M:%S').time().minute * 60 + datetime.datetime.strptime(t, '%H:%M:%S').time().hour * 3600 for t in duration_column_entries[1:]]
        # Calculate average of seconds
        avg_seconds = sum(seconds) / len(seconds)
        # Convert average seconds back to hh:mm:ss format
        avg_time = str(datetime.timedelta(seconds=avg_seconds))
        print(f"Your average workout duration for your {worksheet} workouts is {avg_time}.")
    elif len(duration_column_entries) <= 1:
        print(f"You haven't logged any {worksheet} workouts yet.")

    distance_column_entries = workout_type_to_be_displayed.col_values(3)
    if len(distance_column_entries) >= 4:
        distance_column_last_three_entries = distance_column_entries[-3:]
        distance_column_last_three_entries = [float(entry) for entry in distance_column_entries[1:]]
        avg_distance = sum(distance_column_last_three_entries) / len(distance_column_last_three_entries)
        print(f"Your average distance covered for your last three {worksheet} workouts is {avg_distance}.")
    elif len(distance_column_entries) < 4 and len(distance_column_entries) > 1:
        distance_column_entries = [float(entry) for entry in distance_column_entries[1:]]
        avg_distance = sum(distance_column_entries) / len(distance_column_entries)
        print(f"Your average distance covered for your last three {worksheet} workouts is {avg_distance}.")
    elif len(distance_column_entries) <= 1:
        pass


def validate_user_workout_duration_input(time_data):
    """
    This will ensure that the user may only
    input data in this format - 00:00:00 -
    where the first two digits correspond to hours,
    the second two digits correspond to minutes
    and the last two digist correspond to seconds.
    """
    time_format = re.compile(r'\d\d:\d\d:\d\d')
    while True:
        try:
            time_data_str = str(time_data)
            match = time_format.fullmatch(time_data_str)
            if match is None:
                raise ValueError(
                    f"Your workout time must be entered in this format - 00:00:00. You entered {time_data}"
                    )
            break
        except ValueError as e:
            print(f"Invalid data: {e}, please try again.\n")
            time_data = input("Enter your workout time in this format - 00:00:00: ")
    
    return True


def validate_user_workout_distance_input(distance_data):
    """
    This will ensure that the user may only
    input data in this format - 00.00 -
    the digits correspond to kilometers measured
    to two decimal places.
    """
    distance_format = re.compile(r'\d\d.\d\d')
    while True:
        try:
            distance_data_str = str(distance_data)
            match = distance_format.fullmatch(distance_data_str)
            if match is None:
                raise ValueError(
                    f"Your distance should be entered in this format - 00.00. You entered {distance_data}"
                    )
            break
        except ValueError as e:
            print(f"Invalid data: {e}, please try again.\n")
            distance_data = input("Input your distance covered in kilometres in this format - 00.00 ")
    
    return True


def input_workout_duration_info():
    """
    Here the user will input their
    data for their workout duration.
    """
    while True:
        print("Input your workout duration below\n")
        print("Your time should be entered in this format - 00:00:00\n")
        print("E.g. if your workout was an hour and twenty minutes long, ")
        print("you would enter 01:20:00.\n")
        time_data = input("Please input your workout duration here: ")
        if time_data:
            print("Thank you! Your UT2 Tracker data is being updated.")
            break
    return time_data
        

def input_workout_distance_info():
    """
    Here the user will input their
    data for the distance covered in their workout.
    """
    while True:
        print("Input your distance covered in kilometres below.\n")
        print("Your distance should be entered in this format - 00.00\n")
        print("E.g. if you cycled 23.4km on the exercise bike, ")
        print("you would enter 23.40\n")
        distance_data = input("Please input your workout distance here: ")
        if distance_data:
            print("Thank you! Your UT2 Tracker data is being updated.")
            break
    return distance_data


def update_worksheet(time_data, distance_data, worksheet):
    """
    This function will add the user's workout distance
    and duration data and append it to a row in their
    spreadsheet along with the date of data entry.
    """
    username_sheet = GSPREAD_CLIENT.open(f'{username} UT2 Tracker Spreadsheet')
    worksheet_to_update = username_sheet.worksheet(worksheet)
    current_date = datetime.datetime.now()
    date_string = current_date.strftime("%d-%m-%Y")
    row_to_append = [date_string, time_data, distance_data]
    worksheet_to_update.append_row(row_to_append)
    print(f"{worksheet} worksheet updated successfully.")


def main():
    """
    Run all programme functions
    """
    print("Welcome to Unstoppable UT2, where you can keep track of your UT2 performance. In case you're unfamiliar with the term 'UT2', it refers to an aerobic workout at an intensity which can be held for the full workout duration. You should be comfortable enough to speak and be operating at 65-75% maximimum heart rate. The workout should last approximately 60 minutes.")
    search_file()
    

username = type_username()
main()
