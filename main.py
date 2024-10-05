from openai import OpenAI
from pydantic import BaseModel, Field
import instructor
import json
from datetime import datetime
from typing import Optional

# Die Klasse für die Handhabung des Benutzerprofils und des Ernährungsplans
class Main:
    def __init__(self, user_profile_path):
        # Erstellen eines Instructor-Clients über OpenAI
        self.client = instructor.from_openai(OpenAI())  
        self.user_profile_path = user_profile_path
        self.user_profile = self.load_user_profile()  # Profil laden

    def load_user_profile(self):
        """Lädt das Benutzerprofil aus einer JSON-Datei."""
        with open(self.user_profile_path, 'r') as f:
            return json.load(f)

    def save_user_profile(self):
        """Speichert das Benutzerprofil zurück in die JSON-Datei."""
        with open(self.user_profile_path, 'w') as f:
            json.dump(self.user_profile, f, indent=4)

    def run(self):
        # Initial den Ernährungsplan für heute ausgeben
        response = DietPlanPromt.makePlan(self.client, self.user_profile, "")
        
        # Den erhaltenen Plan speichern
        self.user_profile["diet_plan"][self.get_today_date()] = response.content
        self.save_user_profile()

        # Den Plan von heute ausgeben
        print(f"Ernährungsplan für heute:\n{self.getToday()}")

        # Endlosschleife für Benutzerinput
        while True:
            user_input = input("\nGeben Sie Anpassungen oder Anfragen ein (oder 'exit' zum Beenden): ").strip()
            if user_input.lower() == "exit":
                print("Programm beendet.")
                break

            # Aktualisieren des Ernährungsplans basierend auf dem Benutzerinput
            response = DietPlanPromt.makePlan(self.client, self.user_profile, user_input)
            
            # Den erhaltenen Plan speichern
            self.user_profile["diet_plan"][self.get_today_date()] = response.content
            self.save_user_profile()

            # Den Plan von heute erneut ausgeben
            print(f"\nAktualisierter Ernährungsplan:\n{self.getToday()}")

    def getToday(self):
        """Gibt den Ernährungsplan für den heutigen Tag als String zurück."""
        today = self.get_today_date()
        if today in self.user_profile["diet_plan"]:
            return self.user_profile["diet_plan"][today]
        return "Kein Ernährungsplan für heute gefunden."

    def get_today_date(self):
        """Gibt das heutige Datum als String im Format YYYY-MM-DD zurück."""
        return datetime.now().strftime("%Y-%m-%d")


class DietPlaner(BaseModel):
    content: str = Field(description="Das ist der geupdatete Ernährungsplan für den Nutzer basierend auf seinem Profil.")
    optional_message: Optional[str] = Field(None, description="Optionale Nachricht an den Nutzer")


class DietPlanPromt:
    @staticmethod
    def makePlan(client, user_profile, user_input: str):
        """Erstellt einen Ernährungsplan basierend auf dem Nutzerprofil und optionalem Benutzerinput."""
        return client.chat.completions.create(
            model="gpt-4o",
            max_retries=3,
            messages=[
                {
                    "role": "system",
                    "content": "Erstelle einen Ernährungsplan für den heutigen Tag basierend auf dem Kalorien- und Makronährstoffbedarf und der Anzahl an Mahlzeiten des Nutzers."
                },
                {
                    "role": "user",
                    "content": f"User profile: {user_profile['userProfile']}"
                },
                {
                    "role": "user",
                    "content": user_input  # Benutzerinput wird hier übergeben
                }
            ],
            response_model=DietPlaner  # Validierung durch das Pydantic-Modell
        )


if __name__ == "__main__":
    main = Main("user_profiles/test.json")
    main.run()