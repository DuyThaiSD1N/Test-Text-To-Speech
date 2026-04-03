document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generate-btn');
    const textInput = document.getElementById('text-input');
    const ttsResult = document.getElementById('tts-result');
    const audioPlayer = document.getElementById('audio-player');
    const downloadLink = document.getElementById('download-link');

    async function handleGenerateTTS() {
        const text = textInput.value.trim();
        if (!text) return;

        generateBtn.classList.add('loading');
        generateBtn.disabled = true;

        try {
            const response = await fetch('/api/tts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text }),
            });

            if (!response.ok) throw new Error('Failed to generate audio');

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);

            audioPlayer.src = url;
            downloadLink.href = url;
            ttsResult.classList.remove('hidden');
            audioPlayer.play().catch(e => console.log('Auto-play blocked:', e));

        } catch (error) {
            alert('TTS Error: ' + error.message);
        } finally {
            generateBtn.classList.remove('loading');
            generateBtn.disabled = false;
        }
    }

    generateBtn.addEventListener('click', handleGenerateTTS);
});
