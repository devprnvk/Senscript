const vscode = require('vscode');
const axios = require('axios');

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

	let emotionData = {
		emotion: "neutral",
		duration: 0,
		typingSpeed: 0,
		syntaxErrors: 0,
		windowSwitchCount: 0,
		timestamp: new Date().toISOString()
	};

	const displayEmotionCommand = vscode.commands.registerCommand('sensi-code.displayEmotion', async function () {
		try {
			const response = await axios.get('http://localhost:8080/current_emotion');
			const emotion = response.data.mood;

			let message = '';

			const happyMoods = ['happy']
			const sadAngryMoods = ['sad', 'angry']

			if (happyMoods.includes(emotion)) {
				message = happyMessages[Math.floor(Math.random() * happyMessages.length)];
			} else if (sadAngryMoods.includes(emotion)) {
				message = sadAngryQuotes[Math.floor(Math.random() * sadAngryQuotes.length)];
			} else {
				message = `Your mood is ${emotion}. Keep going!`;
			}

			vscode.window.showInformationMessage(message);

		} catch (error) {
			console.error("Error fetching emotion:", error);
			vscode.window.showErrorMessage("Unable to fetch emotion. Please ensure the server is running.");
		}
	});

	context.subscriptions.push(displayEmotionCommand);

	setInterval(async () => {
		try {
			const response = await axios.get('http://localhost:8080/current_emotion');
			emotionData.emotion = response.data.mood; 

			await axios.post('http://localhost:8080/log', emotionData);
			console.log('Logged data:', emotionData);

		} catch (error) {
			console.error("Error logging emotion data:", error);
		}
	}, 5000);

	vscode.workspace.onDidChangeTextDocument(() => {
		emotionData.typingSpeed++;
	});

	vscode.languages.onDidChangeDiagnostics((event) => {
		emotionData.syntaxErrors = event.uris.map(uri => vscode.languages.getDiagnostics(uri))
			.flat().filter(d => d.severity === vscode.DiagnosticSeverity.Error).length;
	});

	let lastWindowSwitchTime = Date.now();
	vscode.window.onDidChangeActiveTextEditor(() => {
		let now = Date.now();
		emotionData.windowSwitchCount++;
		emotionData.duration = now - lastWindowSwitchTime;
		lastWindowSwitchTime = now;
	});
}

function deactivate() { }

module.exports = {
	activate,
	deactivate
};
