import csv
import io
import time
import requests

# ==========================================
# CONFIGURATION
# ==========================================

# 1. Google Sheets browser URL
GOOGLE_SHEET_URL = 'https://docs.google.com/spreadsheets/d/1ODZszcI75dRFgVCmwfNuBB_9hbaaRLu4orWM9tZHDnQ/edit?usp=sharing'

# 2. Notepad output file
OUTPUT_FILE = 'chess_ratings_report.txt'

# 3. Google Sheet column headers
NAME_COLUMN_HEADER = 'Name'
USERNAME_COLUMN_HEADER = 'chess.com username'
PHONE_COLUMN_HEADER = 'Phone number'
ENROLLMENT_COLUMN_HEADER = 'Enrollment Number'


def convert_sheet_url_to_csv(url):
    """Converts a standard Google Sheets sharing link into a direct CSV download link."""
    if '/edit' in url:
        base_url = url.split('/edit')[0]
        return f'{base_url}/export?format=csv'

    return url


def fetch_ratings_from_sheet():

    csv_url = convert_sheet_url_to_csv(GOOGLE_SHEET_URL)

    headers = {
        'User-Agent': 'ChessRatingFetcher/2.0 (contact: jayeshy2806@gmail.com)'
    }

    print('⏳ Downloading player list from Google Sheet...')

    try:

        response = requests.get(csv_url)

        if response.status_code != 200:
            print(
                f"❌ Failed to download sheet data. "
                f"Status: {response.status_code}"
            )
            return

        # ==========================================
        # READ GOOGLE SHEET CSV
        # ==========================================

        csv_file = io.StringIO(response.text)
        reader = csv.DictReader(csv_file)

        # ==========================================
        # CLEAN COLUMN HEADERS
        # ==========================================

        cleaned_fields = {
            name.strip().lower(): name
            for name in reader.fieldnames
            if name
        }

        target_name_key = NAME_COLUMN_HEADER.strip().lower()
        target_user_key = USERNAME_COLUMN_HEADER.strip().lower()
        target_phone_key = PHONE_COLUMN_HEADER.strip().lower()
        target_enrollment_key = ENROLLMENT_COLUMN_HEADER.strip().lower()

        # ==========================================
        # CHECK REQUIRED COLUMNS
        # ==========================================

        if target_name_key not in cleaned_fields:
            print(
                f"❌ Error: Could not find column matching "
                f"'{NAME_COLUMN_HEADER}'."
            )
            print(
                f"Available columns found: "
                f"{list(cleaned_fields.values())}"
            )
            return

        if target_user_key not in cleaned_fields:
            print(
                f"❌ Error: Could not find column matching "
                f"'{USERNAME_COLUMN_HEADER}'."
            )
            print(
                f"Available columns found: "
                f"{list(cleaned_fields.values())}"
            )
            return

        if target_phone_key not in cleaned_fields:
            print(
                f"❌ Error: Could not find column matching "
                f"'{PHONE_COLUMN_HEADER}'."
            )
            print(
                f"Available columns found: "
                f"{list(cleaned_fields.values())}"
            )
            return

        if target_enrollment_key not in cleaned_fields:
            print(
                f"❌ Error: Could not find column matching "
                f"'{ENROLLMENT_COLUMN_HEADER}'."
            )
            print(
                f"Available columns found: "
                f"{list(cleaned_fields.values())}"
            )
            return

        # ==========================================
        # GET ACTUAL COLUMN HEADERS
        # ==========================================

        actual_name_header = cleaned_fields[target_name_key]
        actual_user_header = cleaned_fields[target_user_key]
        actual_phone_header = cleaned_fields[target_phone_key]
        actual_enrollment_header = cleaned_fields[target_enrollment_key]

        # ==========================================
        # STORE ALL PLAYERS
        # ==========================================

        players = []

        print('♟️ Processing players...')

        for row in reader:

            # --------------------------------------
            # NAME
            # --------------------------------------

            player_name = (
                row.get(actual_name_header, '').strip()
                if row.get(actual_name_header)
                else 'Unknown'
            )

            # --------------------------------------
            # CHESS.COM USERNAME
            # --------------------------------------

            username = row.get(actual_user_header, '').strip()

            # --------------------------------------
            # PHONE NUMBER
            # --------------------------------------

            phone_number = (
                row.get(actual_phone_header, '').strip()
                if row.get(actual_phone_header)
                else 'Not Provided'
            )

            # --------------------------------------
            # ENROLLMENT NUMBER
            # --------------------------------------

            enrollment_number = (
                row.get(actual_enrollment_header, '').strip()
                if row.get(actual_enrollment_header)
                else 'Not Provided'
            )

            # Skip rows where username is missing
            if not username:
                continue

            # ==========================================
            # CHESS.COM API
            # ==========================================

            api_url = (
                f'https://api.chess.com/pub/player/'
                f'{username}/stats'
            )

            try:

                api_response = requests.get(
                    api_url,
                    headers=headers
                )

                if api_response.status_code == 200:

                    data = api_response.json()

                    # ----------------------------------
                    # RAPID RATING
                    # ----------------------------------

                    rapid_rating = (
                        data.get('chess_rapid', {})
                        .get('last', {})
                        .get('rating', None)
                    )

                    # ----------------------------------
                    # BLITZ RATING
                    # ----------------------------------

                    blitz_rating = (
                        data.get('chess_blitz', {})
                        .get('last', {})
                        .get('rating', None)
                    )

                elif api_response.status_code == 404:

                    rapid_rating = None
                    blitz_rating = None

                else:

                    rapid_rating = None
                    blitz_rating = None

            except Exception:

                rapid_rating = None
                blitz_rating = None

            # ==========================================
            # STORE PLAYER DATA
            # ==========================================

            players.append({
                'name': player_name,
                'username': username,
                'enrollment': enrollment_number,
                'phone': phone_number,
                'rapid': rapid_rating,
                'blitz': blitz_rating
            })

            print(
                f'✅ Processed: {username} '
                f'({player_name})'
            )

            # Short pause to follow Chess.com API rules
            time.sleep(0.2)

        # ==========================================
        # SORT BY RAPID RATING
        # HIGHEST TO LOWEST
        # ==========================================

        players.sort(
            key=lambda player: (
                player['rapid'] is not None,
                player['rapid']
                if player['rapid'] is not None
                else 0
            ),
            reverse=True
        )

        # ==========================================
        # WRITE SORTED DATA TO TEXT FILE
        # ==========================================

        with open(
            OUTPUT_FILE,
            'w',
            encoding='utf-8'
        ) as output_file:

            output_file.write(
                '=' * 60 + '\n'
            )

            output_file.write(
                '🏆 CHESS.COM RATINGS REPORT\n'
            )

            output_file.write(
                '=' * 60 + '\n\n'
            )

            # ==========================================
            # WRITE EACH PLAYER
            # ==========================================

            for rank, player in enumerate(
                players,
                start=1
            ):

                # Display Rapid rating
                if player['rapid'] is not None:
                    rapid_rating = player['rapid']
                else:
                    rapid_rating = 'Unrated'

                # Display Blitz rating
                if player['blitz'] is not None:
                    blitz_rating = player['blitz']
                else:
                    blitz_rating = 'Unrated'

                # ==========================================
                # REPORT ENTRY
                # ==========================================

                log_entry = (
                    f"🏅 Rank: {rank}\n"
                    f"👤 Name: {player['name']}\n"
                    f"🎓 Enrollment Number: "
                    f"{player['enrollment']}\n"
                    f"📞 Phone number: "
                    f"{player['phone']}\n"
                    f"🆔 Username: "
                    f"{player['username']}\n"
                    f"⚡ Blitz Rating: "
                    f"{blitz_rating}\n"
                    f"⏱️ Rapid Rating: "
                    f"{rapid_rating}\n"
                    f"{'-' * 40}\n"
                )

                output_file.write(log_entry)

        print(
            f'\n🎉 Complete! '
            f'Notepad file generated: {OUTPUT_FILE}'
        )

    except requests.exceptions.RequestException as e:

        print(
            f'🔌 Connection failed: {e}'
        )


# ==========================================
# PROGRAM START
# ==========================================

if __name__ == '__main__':
    fetch_ratings_from_sheet()
