const form = document.getElementById('uploadForm');
const audioPlayer = document.getElementById('audioPlayer');
const fileInput = document.getElementById('fileInput');
const togglePlayPauseButton = document.getElementById('togglePlayPauseButton');
const downloadButton = document.getElementById('downloadButton');
const rewindButton = document.getElementById('rewindButton');
const forwardButton = document.getElementById('forwardButton');
const playbackSpeedButton = document.getElementById('playbackSpeedButton');
const fileLabel = document.querySelector('label[for="fileInput"]');
const languageSelect = document.getElementById('languageSelect');
const liveRegion = document.getElementById('liveRegion');
const progressBar = document.getElementById('progressBar');
const uploadedImage = document.getElementById('uploadedImage');
const highlightBox = document.getElementById('highlightBox');
const popup = document.getElementById('popup');
const closeButton = document.querySelector('.close-button');

const translations = {
    en: {
        selectFile: 'Select File',
        makeMagic: 'Make Magic',
        play: 'Play',
        pause: 'Pause',
        rewind: 'Rewind',
        forward: 'Forward',
        download: 'Download',
        speed: 'Speed: 1x'
    },
    uk: {
        selectFile: 'Вибрати файл',
        makeMagic: 'Створити магію',
        play: 'Відтворити',
        pause: 'Пауза',
        rewind: 'Перемотати назад',
        forward: 'Перемотати вперед',
        download: 'Завантажити',
        speed: 'Швидкість: 1x'
    },
    ru: {
        selectFile: 'Выбрать файл',
        makeMagic: 'Создать магию',
        play: 'Старт',
        pause: 'Пауза',
        rewind: 'Перемотать назад',
        forward: 'Перемотать вперед',
        download: 'Скачать',
        speed: 'Скорость: 1x'
    },
    es: {
        selectFile: 'Seleccionar archivo',
        makeMagic: 'Hacer magia',
        play: 'Reproducir',
        pause: 'Pausa',
        rewind: 'Rebobinar',
        forward: 'Adelantar',
        download: 'Descargar',
        speed: 'Velocidad: 1x'
    }
};

const updateInterfaceLanguage = (lang) => {
    fileLabel.textContent = translations[lang].selectFile;
    document.getElementById('makeMagicButton').textContent = translations[lang].makeMagic;
    togglePlayPauseButton.textContent = translations[lang].play;
    rewindButton.textContent = translations[lang].rewind;
    forwardButton.textContent = translations[lang].forward;
    downloadButton.textContent = translations[lang].download;
    playbackSpeedButton.textContent = translations[lang].speed;
};

const setUpLanguage = (lang) => {
    if (translations[lang]) {
        updateInterfaceLanguage(lang);
    } else {
        updateInterfaceLanguage('en');
    }
};

languageSelect.addEventListener('change', function() {
    setUpLanguage(languageSelect.value);
});

// Example setting language after processing OCR or user selects the language from the selector
setUpLanguage('en'); // Default to English, can be set dynamically as needed

fileInput.addEventListener('change', function() {
    fileLabel.textContent = fileInput.files[0].name;
});

form.addEventListener('submit', function(event) {
    event.preventDefault();
    const formData = new FormData(form);
    resetAudioPlayer();

    let originalFileName = fileInput.files[0]?.name.split('.').slice(0, -1).join('.') || generateUUID();
    let audioFileName = `${originalFileName}.mp3`;

    // Handling the upload and text extraction
    fetch('/upload-image', {
        method: 'POST',
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            liveRegion.textContent = 'Error processing image: ' + data.error;
            return;
        }
        if (data.text) {
            // Show the uploaded image
            const imageUrl = URL.createObjectURL(fileInput.files[0]);
            uploadedImage.src = imageUrl;
            uploadedImage.style.display = 'block';

            // Open the popup
            popup.style.display = 'block';

            // Reset file input
            document.getElementById('fileInput').value = '';
            fileLabel.textContent = translations[languageSelect.value]?.selectFile || 'Select File';
            // Generating speech from extracted text
            return fetch('/synthesize-speech', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: data.text,
                    language: languageSelect.value
                })
            });
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to generate speech.');
        }
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        audioPlayer.src = url;

        // Set the href and download attributes for the Download button
        downloadButton.href = url;
        downloadButton.setAttribute('download', audioFileName);

        // Automatically play the audio
        audioPlayer.play();
        togglePlayPauseButton.innerText = translations[languageSelect.value].pause;
        liveRegion.textContent = 'Playing audio';

        togglePlayPauseButton.onclick = () => {
            if (audioPlayer.paused) {
                audioPlayer.play();
                togglePlayPauseButton.innerText = translations[languageSelect.value].pause;
                liveRegion.textContent = 'Playing audio';
            } else {
                audioPlayer.pause();
                togglePlayPauseButton.innerText = translations[languageSelect.value].play;
                liveRegion.textContent = 'Audio paused';
            }
        };

        rewindButton.onclick = () => {
            audioPlayer.currentTime -= 5; // Rewind 5 seconds
            liveRegion.textContent = `Jumped to ${audioPlayer.currentTime.toFixed(2)} seconds`;
        };

        forwardButton.onclick = () => {
            audioPlayer.currentTime += 5; // Forward 5 seconds
            liveRegion.textContent = `Jumped to ${audioPlayer.currentTime.toFixed(2)} seconds`;
        };

        let playbackSpeeds = [0.75, 1, 1.25];
        playbackSpeedButton.onclick = () => {
            let currentSpeed = audioPlayer.playbackRate;
            let newSpeedIndex = (playbackSpeeds.indexOf(currentSpeed) + 1) % playbackSpeeds.length;
            let newSpeed = playbackSpeeds[newSpeedIndex];
            audioPlayer.playbackRate = newSpeed;
            playbackSpeedButton.textContent = `${translations[languageSelect.value]?.speed.split(":")[0] || 'Speed'}: ${newSpeed}x`;
            liveRegion.textContent = `Playback speed changed to ${newSpeed}x`;
        };

        // Update progress bar as audio plays
        audioPlayer.addEventListener('timeupdate', () => {
            progressBar.value = (audioPlayer.currentTime / audioPlayer.duration) * 100;
            highlightCurrentText(audioPlayer.currentTime);
        });

        // Keyboard navigation for audio controls
        document.onkeydown = (e) => {
            if (e.key === 'ArrowLeft') {
                audioPlayer.currentTime -= 5; // Rewind 5 seconds
                liveRegion.textContent = `Jumped to ${audioPlayer.currentTime.toFixed(2)} seconds`;
                e.preventDefault();
            } else if (e.key === 'ArrowRight') {
                audioPlayer.currentTime += 5; // Forward 5 seconds
                liveRegion.textContent = `Jumped to ${audioPlayer.currentTime.toFixed(2)} seconds`;
                e.preventDefault();
            } else if (e.key === ' ') {
                if (audioPlayer.paused) {
                    audioPlayer.play();
                    togglePlayPauseButton.innerText = translations[languageSelect.value].pause;
                    liveRegion.textContent = 'Playing audio';
                } else {
                    audioPlayer.pause();
                    togglePlayPauseButton.innerText = translations[languageSelect.value].play;
                    liveRegion.textContent = 'Audio paused';
                }
                e.preventDefault();
            }
        };
    })
    .catch(err => {
        console.error('Error occurred:', err);
        liveRegion.textContent = 'Error during processing: ' + err.message;
    });
});

function resetAudioPlayer() {
    audioPlayer.src = '';
    audioPlayer.pause();
    audioPlayer.currentTime = 0;
    togglePlayPauseButton.innerText = translations[languageSelect.value]?.play || 'Play';
    downloadButton.hidden = true;
    playbackSpeedButton.hidden = true;
    rewindButton.hidden = true;
    forwardButton.hidden = true;
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0,
            v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function highlightCurrentText(currentTime) {
    // Assuming we have a function getWordTimeMapping() that returns an array of times for each word
    const wordTimes = getWordTimeMapping(); // This function needs to be implemented based on your audio synthesis

    // Example: let's assume wordTimes is an array of objects with word and bounding box coordinates
    // [{time: 0, x: 10, y: 20, width: 100, height: 20}, ...]

    const currentWord = wordTimes.find((word, index) => {
        return currentTime >= word.time && (index === wordTimes.length - 1 || currentTime < wordTimes[index + 1].time);
    });

    if (currentWord) {
        highlightBox.style.left = `${currentWord.x}px`;
        highlightBox.style.top = `${currentWord.y}px`;
        highlightBox.style.width = `${currentWord.width}px`;
        highlightBox.style.height = `${currentWord.height}px`;
        highlightBox.style.display = 'block';
    } else {
        highlightBox.style.display = 'none';
    }
}

function getWordTimeMapping() {
    // Placeholder function - implement your logic to map word times and bounding boxes
    // Example: return [{time: 0, x: 10, y: 20, width: 100, height: 20}, ...];
    return [];
}

// Close the popup when the close button is clicked
closeButton.addEventListener('click', () => {
    popup.style.display = 'none';
});

// Close the popup when clicking outside of the popup content
window.addEventListener('click', (event) => {
    if (event.target == popup) {
        popup.style.display = 'none';
    }
});