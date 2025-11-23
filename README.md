# Minecraft Stats & Advancements Dashboard
 A tool that tracks Minecraft Stats and Advancements from a live server by parsing user stat/advancement(.json) files and then using it to create visualizations. 

Visit:
https://minecraftstatstracker.com/
to see it in action on a live server!

# Features
- **Dual Edition Support**: Automatically detects and fetches metadata for Java (Mojang API) and Bedrock (OpenXBL API) players.
- **Interactive Charts**: Built with Chart.js to visualize data via Bar, Pie, Line, Radar, and Doughnut charts.
- **Stat Selections**: Compare specific stats (categorized)
 <img width="25%" height="25%" alt="Screenshot 2025-11-22 212713" src="https://github.com/user-attachments/assets/29eaa521-4dc0-4870-86f1-2aa0073e4950" />

- **Data Upload**: Allows users to input their own stats and advancement JSON files
<img width="25%" height="25%" alt="image" src="https://github.com/user-attachments/assets/dd4118fe-1912-4d28-bd10-0dda052d180f" />

- **Common Data**: Retrieve common data of selected players
- **Functions**: Sort by most in count, sort chart by count

# Tech Involved
- **Backend**: Python, Flask
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Visualization**: Chart.js, CharDataLabels
- **API's**: Mojang (Java uuid to names), OpenXBL (Bedrock xuid to names)

# Clone/Download
I'd recommend visiting [here](https://minecraftstatstracker.com/) and inputing your own json data but if you want to run it locally I have the work in progress here.

1. Clone or Download
Download the project files to your local machine.

2. Install Dependencies (python 3.8+)
`pip install flask flask-cors requests`

3. Configure Paths
Open minecraft_stats_analyzer.py and update the project_folder variable to match your local directory structure:
`project_folder = '/path/to/your/MinecraftStatsTracker'`

<img width="50%" height="50%" alt="image" src="https://github.com/user-attachments/assets/a40204c6-6769-4fb5-8fd1-e12522d7aac9" />

Make sure to include your data/json files in the data folder

# Usage
1. Run using
`python minecraft_stats_analyzer.py`

2. Navigate to
`http://localhost:5000`




