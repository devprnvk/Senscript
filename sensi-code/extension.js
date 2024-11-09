const vscode = require('vscode');
const axios = require('axios');  // Use axios for HTTP requests

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

			// Display emotion in the VS Code info message
			vscode.window.showInformationMessage(`Current Emotion: ${emotion}`);
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
