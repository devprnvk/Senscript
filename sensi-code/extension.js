const vscode = require('vscode');
const axios = require('axios');  // Use axios for HTTP requests

const happyMessages = [
	"You're doing great! Keep it up!",
	"The best is yet to come!",
	"You're on fire today! Keep pushing!",
	"Great things are happening to you!"
];


const sadAngryQuotes = [
	"Every day may not be good, but there's something good in every day.",
	"Don't let yesterday take up too much of today.",
	"When you feel like quitting, think about why you started.",
	"Difficult roads often lead to beautiful destinations."
];

function activate(context) {
	console.log('Sensi-code extension is now active!');

	// Track the current emotion data
	let emotionData = {
		emotion: "neutral",  // Initial emotion (can be dynamically updated)
		duration: 0,
		typingSpeed: 0,
		syntaxErrors: 0,
		windowSwitchCount: 0,
		timestamp: new Date().toISOString()
	};

	// Command to fetch and display current emotion
	const displayEmotionCommand = vscode.commands.registerCommand('sensi-code.displayEmotion', async function () {
		try {
			// Fetch current emotion from the server
			const response = await axios.get('http://localhost:8080/current_emotion');
			const emotion = response.data.mood;

			// Decide the message based on the mood
			let message = '';

			// Check if mood is a happy one
			const happyMoods = ['happy']
			const sadAngryMoods = ['sad', 'angry']

			if (happyMoods.includes(emotion)) {
				// Randomly pick a message from the happyMessages array
				message = happyMessages[Math.floor(Math.random() * happyMessages.length)];
			} else if (sadAngryMoods.includes(emotion)) {
				// Randomly pick a quote from the sadAngryQuotes array
				message = sadAngryQuotes[Math.floor(Math.random() * sadAngryQuotes.length)];
			} else {
				// If mood doesn't match, do nothing
				message = `Your mood is ${emotion}. Keep going!`;
			}

			vscode.window.showInformationMessage(message);

		} catch (error) {
			console.error("Error fetching emotion:", error);
			vscode.window.showErrorMessage("Unable to fetch emotion. Please ensure the server is running.");
		}
	});

	context.subscriptions.push(displayEmotionCommand);

	// Periodically update emotion
	setInterval(async () => {
		try {
			const response = await axios.get('http://localhost:8080/current_emotion');
			emotionData.emotion = response.data.mood;  // Update emotion

			// Send the emotion data to the server
			await axios.post('http://localhost:8080/log', emotionData);
			console.log('Logged data:', emotionData);  // Confirm logging in the console

		} catch (error) {
			console.error("Error logging emotion data:", error);
		}
	}, 5000);  // Update every 5 seconds

	// Track typing speed (for example, track keystrokes per event)
	vscode.workspace.onDidChangeTextDocument(() => {
		emotionData.typingSpeed++;
	});

	// Track syntax errors
	vscode.languages.onDidChangeDiagnostics((event) => {
		emotionData.syntaxErrors = event.uris.map(uri => vscode.languages.getDiagnostics(uri))
			.flat().filter(d => d.severity === vscode.DiagnosticSeverity.Error).length;
	});

	// Track window switches (simplified)
	let lastWindowSwitchTime = Date.now();
	vscode.window.onDidChangeActiveTextEditor(() => {
		let now = Date.now();
		emotionData.windowSwitchCount++;  // Increment window switch count
		emotionData.duration = now - lastWindowSwitchTime;  // Track how long the editor was in focus
		lastWindowSwitchTime = now;
	});
}

function deactivate() { }

module.exports = {
	activate,
	deactivate
};
