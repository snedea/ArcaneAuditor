// Arcane Auditor Learning Game
// Main Game Logic

class ArcaneAuditorGame {
    constructor() {
        this.currentCategory = 'all';
        this.currentDifficulty = 'easy';
        this.score = 0;
        this.streak = 0;
        this.bestStreak = 0;
        this.questionsAnswered = 0;
        this.correctAnswers = 0;
        this.currentQuestionIndex = 0;
        this.questions = [];
        this.rulesCompleted = new Set();
        this.timer = null;
        this.timeRemaining = 30;

        this.init();
    }

    init() {
        this.initializeTheme();
        this.loadHighScore();
        this.setupEventListeners();
        this.updateDashboard();
    }

    setupEventListeners() {
        // Category selection
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
                e.currentTarget.classList.add('active');
                this.currentCategory = e.currentTarget.dataset.category;
            });
        });

        // Difficulty selection
        document.querySelectorAll('.difficulty-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.difficulty-btn').forEach(b => b.classList.remove('active'));
                e.currentTarget.classList.add('active');
                this.currentDifficulty = e.currentTarget.dataset.difficulty;
            });
        });

        // Start game
        document.getElementById('start-game').addEventListener('click', () => {
            this.startGame();
        });

        // Submit answer
        document.getElementById('submit-answer').addEventListener('click', () => {
            this.submitAnswer();
        });

        // Next question
        document.getElementById('next-question').addEventListener('click', () => {
            this.nextQuestion();
        });

        // Back to menu
        document.querySelectorAll('.menu-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.backToMenu();
            });
        });

        // Play again
        document.getElementById('play-again').addEventListener('click', () => {
            this.startGame();
        });
    }

    startGame() {
        // Reset game state
        this.score = 0;
        this.streak = 0;
        this.questionsAnswered = 0;
        this.correctAnswers = 0;
        this.currentQuestionIndex = 0;
        this.rulesCompleted.clear();

        // Generate questions based on category
        this.questions = this.generateQuestions();

        // Show quiz screen
        this.showScreen('quiz-screen');
        this.loadQuestion();
        this.updateDashboard();
    }

    generateQuestions() {
        const questions = [];
        let rules = [];

        // Select rules based on category
        if (this.currentCategory === 'script') {
            rules = RULES_DATA.scriptRules;
        } else if (this.currentCategory === 'structure') {
            rules = RULES_DATA.structureRules;
        } else {
            rules = [...RULES_DATA.scriptRules, ...RULES_DATA.structureRules];
        }

        // Shuffle and select 10 random rules
        const shuffled = this.shuffleArray([...rules]);
        const selectedRules = shuffled.slice(0, 10);

        // Generate question for each rule based on difficulty
        selectedRules.forEach(rule => {
            const question = this.generateQuestion(rule);
            if (question) {
                questions.push(question);
            }
        });

        return questions;
    }

    generateQuestion(rule) {
        const questionTypes = {
            easy: ['trueFalse', 'whyMatters', 'severity'],
            medium: ['identifyViolation', 'identifyFix'],
            hard: ['codeComparison', 'multipleRules']
        };

        const types = questionTypes[this.currentDifficulty];
        const type = types[Math.floor(Math.random() * types.length)];

        const generators = {
            trueFalse: () => this.generateTrueFalse(rule),
            whyMatters: () => this.generateWhyMatters(rule),
            severity: () => this.generateSeverity(rule),
            identifyViolation: () => this.generateIdentifyViolation(rule),
            identifyFix: () => this.generateIdentifyFix(rule),
            codeComparison: () => this.generateCodeComparison(rule),
            multipleRules: () => this.generateMultipleRules(rule)
        };

        return generators[type]();
    }

    generateTrueFalse(rule) {
        const statements = [
            {
                text: `The ${rule.name} has ${rule.severity} severity.`,
                correct: true
            },
            {
                text: `The ${rule.name} belongs to the ${rule.category} Rules category.`,
                correct: true
            },
            {
                text: `The ${rule.name} has ${rule.severity === 'ACTION' ? 'ADVICE' : 'ACTION'} severity.`,
                correct: false
            }
        ];

        const statement = statements[Math.floor(Math.random() * statements.length)];

        return {
            type: 'trueFalse',
            rule: rule,
            text: statement.text,
            answers: [
                { text: 'True', correct: statement.correct },
                { text: 'False', correct: !statement.correct }
            ]
        };
    }

    generateWhyMatters(rule) {
        return {
            type: 'whyMatters',
            rule: rule,
            text: `Why does the ${rule.name} matter?`,
            answers: [
                { text: rule.whyMatters, correct: true },
                { text: 'It helps make code run faster by optimizing loops', correct: false },
                { text: 'It ensures compatibility with older browsers', correct: false },
                { text: 'It reduces memory usage by compressing variables', correct: false }
            ].sort(() => Math.random() - 0.5)
        };
    }

    generateSeverity(rule) {
        return {
            type: 'severity',
            rule: rule,
            text: `What is the severity level of ${rule.name}?`,
            answers: [
                { text: 'ACTION 🚨', correct: rule.severity === 'ACTION' },
                { text: 'ADVICE ℹ️', correct: rule.severity === 'ADVICE' }
            ]
        };
    }

    generateIdentifyViolation(rule) {
        return {
            type: 'identifyViolation',
            rule: rule,
            text: `Which code example violates the ${rule.name}?`,
            showCode: true,
            answers: [
                { text: 'Code Example A', code: this.stripHintComments(rule.violationExample), correct: true },
                { text: 'Code Example B', code: this.stripHintComments(rule.fixExample), correct: false }
            ].sort(() => Math.random() - 0.5)
        };
    }

    generateIdentifyFix(rule) {
        return {
            type: 'identifyFix',
            rule: rule,
            text: `What is the correct fix for this ${rule.name} violation?`,
            codeExample: this.stripHintComments(rule.violationExample),
            answers: [
                { text: 'Fix A', code: this.stripHintComments(rule.fixExample), correct: true },
                { text: 'Fix B', code: this.stripHintComments(rule.violationExample), correct: false }
            ].sort(() => Math.random() - 0.5)
        };
    }

    generateCodeComparison(rule) {
        return {
            type: 'codeComparison',
            rule: rule,
            text: `Review this code. What rule does it violate?`,
            codeExample: this.stripHintComments(rule.violationExample),
            answers: [
                { text: rule.name, correct: true },
                { text: this.getRandomRule(rule).name, correct: false },
                { text: this.getRandomRule(rule).name, correct: false },
                { text: 'No violation detected', correct: false }
            ].sort(() => Math.random() - 0.5)
        };
    }

    generateMultipleRules(rule) {
        const catches = rule.catches;
        const correctCatch = catches[Math.floor(Math.random() * catches.length)];

        return {
            type: 'multipleRules',
            rule: rule,
            text: `What does the ${rule.name} catch?`,
            answers: [
                { text: correctCatch, correct: true },
                { text: 'Undefined variables in global scope', correct: false },
                { text: 'Missing semicolons in statement blocks', correct: false },
                { text: 'Incorrect import statements', correct: false }
            ].sort(() => Math.random() - 0.5)
        };
    }

    getRandomRule(excludeRule) {
        const allRules = [...RULES_DATA.scriptRules, ...RULES_DATA.structureRules];
        const filtered = allRules.filter(r => r.id !== excludeRule.id);
        return filtered[Math.floor(Math.random() * filtered.length)];
    }

    stripHintComments(code) {
        // Remove lines or inline comments with emoji hints (❌ ✅)
        return code
            .split('\n')
            .map(line => {
                // Remove inline comments with emojis
                return line.replace(/\s*\/\/\s*[❌✅].*$/, '');
            })
            .join('\n')
            .trim();
    }

    loadQuestion() {
        if (this.currentQuestionIndex >= this.questions.length) {
            this.showFinalScreen();
            return;
        }

        const question = this.questions[this.currentQuestionIndex];

        // Update question counter
        document.getElementById('question-number').textContent = this.currentQuestionIndex + 1;
        document.getElementById('total-questions').textContent = this.questions.length;

        // Update rule badge
        const severityBadge = document.getElementById('severity-badge');
        severityBadge.textContent = question.rule.severity;
        severityBadge.className = `severity-badge ${question.rule.severity.toLowerCase()}`;

        document.getElementById('category-badge').textContent = question.rule.category;

        // Update question text
        document.getElementById('question-text').textContent = question.text;

        // Update rule name
        document.getElementById('rule-name').textContent = `Rule: ${question.rule.name}`;

        // Show code example if needed
        const codeContainer = document.getElementById('code-example-container');
        if (question.codeExample) {
            document.getElementById('code-example').textContent = question.codeExample;
            codeContainer.style.display = 'block';
        } else {
            codeContainer.style.display = 'none';
        }

        // Render answers
        this.renderAnswers(question);

        // Start timer
        this.startTimer();
    }

    renderAnswers(question) {
        const container = document.getElementById('answers-container');
        container.innerHTML = '';

        question.answers.forEach((answer, index) => {
            const button = document.createElement('button');
            button.className = 'answer-btn';
            button.dataset.index = index;
            button.dataset.correct = answer.correct;

            const textDiv = document.createElement('div');
            textDiv.textContent = answer.text;
            button.appendChild(textDiv);

            if (answer.code) {
                const codeDiv = document.createElement('div');
                codeDiv.className = 'answer-code';
                codeDiv.textContent = answer.code;
                button.appendChild(codeDiv);
            }

            button.addEventListener('click', () => this.selectAnswer(button));
            container.appendChild(button);
        });

        document.getElementById('submit-answer').disabled = true;
    }

    selectAnswer(button) {
        // Deselect all
        document.querySelectorAll('.answer-btn').forEach(btn => {
            btn.classList.remove('selected');
        });

        // Select clicked
        button.classList.add('selected');
        this.selectedAnswer = button;
        document.getElementById('submit-answer').disabled = false;
    }

    submitAnswer() {
        clearInterval(this.timer);

        const isCorrect = this.selectedAnswer.dataset.correct === 'true';
        const question = this.questions[this.currentQuestionIndex];

        // Disable all buttons
        document.querySelectorAll('.answer-btn').forEach(btn => {
            btn.disabled = true;
            if (btn.dataset.correct === 'true') {
                btn.classList.add('correct');
            }
            if (btn === this.selectedAnswer && !isCorrect) {
                btn.classList.add('incorrect');
            }
        });

        // Update score and stats
        this.questionsAnswered++;

        if (isCorrect) {
            this.correctAnswers++;
            this.streak++;
            this.bestStreak = Math.max(this.bestStreak, this.streak);

            // Calculate score with time bonus
            const timeBonus = Math.floor(this.timeRemaining / 3);
            const streakBonus = this.streak * 10;
            const points = 100 + timeBonus + streakBonus;
            this.score += points;

            this.rulesCompleted.add(question.rule.id);
        } else {
            this.streak = 0;
        }

        this.updateDashboard();

        // Show result screen
        setTimeout(() => {
            this.showResultScreen(isCorrect, question);
        }, 1500);
    }

    showResultScreen(isCorrect, question) {
        const resultIcon = document.getElementById('result-icon');
        const resultTitle = document.getElementById('result-title');
        const resultMessage = document.getElementById('result-message');

        if (isCorrect) {
            resultIcon.textContent = '🎉';
            resultTitle.textContent = 'Correct!';
            resultTitle.style.color = '#00b894';

            const timeBonus = Math.floor(this.timeRemaining / 3);
            const streakBonus = this.streak * 10;
            const points = 100 + timeBonus + streakBonus;

            resultMessage.textContent = `You earned ${points} points! (Base: 100, Time: +${timeBonus}, Streak: +${streakBonus})`;
        } else {
            resultIcon.textContent = '❌';
            resultTitle.textContent = 'Incorrect';
            resultTitle.style.color = '#d63031';
            resultMessage.textContent = 'Don\'t worry! Let\'s learn from this.';
        }

        // Populate comprehensive rule details
        const rule = question.rule;

        // Rule name and meta
        document.getElementById('rule-detail-name').textContent = rule.name;
        const severityBadge = document.getElementById('rule-detail-severity');
        severityBadge.textContent = `${rule.severity === 'ACTION' ? '🚨' : 'ℹ️'} ${rule.severity}`;
        severityBadge.className = `rule-severity ${rule.severity.toLowerCase()}`;
        document.getElementById('rule-detail-category').textContent = rule.category;
        document.getElementById('rule-detail-description').textContent = rule.description;

        // Applies to (if exists)
        if (rule.appliesTo) {
            document.getElementById('rule-applies-to').textContent = rule.appliesTo;
            document.getElementById('rule-applies-to-section').style.display = 'block';
        } else {
            document.getElementById('rule-applies-to-section').style.display = 'none';
        }

        // Configurable (if exists)
        if (rule.configurable !== undefined) {
            const configurableText = rule.configurable ? '✅ Custom settings available' : '❌ Not configurable';
            document.getElementById('rule-configurable').textContent = configurableText;
            document.getElementById('rule-configurable-section').style.display = 'block';
        } else {
            document.getElementById('rule-configurable-section').style.display = 'none';
        }

        // What it catches (as bulleted list)
        const catchesList = document.getElementById('catches-list');
        catchesList.innerHTML = '';
        rule.catches.forEach(catchItem => {
            const li = document.createElement('li');
            li.textContent = catchItem;
            catchesList.appendChild(li);
        });

        // Smart exclusions (if exists)
        if (rule.smartExclusions) {
            document.getElementById('smart-exclusions').textContent = rule.smartExclusions;
            document.getElementById('smart-exclusions-section').style.display = 'block';
        } else {
            document.getElementById('smart-exclusions-section').style.display = 'none';
        }

        // Why this matters
        document.getElementById('why-matters').textContent = rule.whyMatters;

        // Configuration example (if exists)
        if (rule.configurationExample) {
            document.getElementById('config-example').textContent = rule.configurationExample;
            document.getElementById('config-example-section').style.display = 'block';
        } else {
            document.getElementById('config-example-section').style.display = 'none';
        }

        // Code comparison (with hints preserved for learning)
        document.getElementById('violation-code').textContent = rule.violationExample;
        document.getElementById('fix-code').textContent = rule.fixExample;

        this.showScreen('result-screen');
    }

    nextQuestion() {
        this.currentQuestionIndex++;
        this.showScreen('quiz-screen');
        this.loadQuestion();
    }

    startTimer() {
        this.timeRemaining = 30;
        const timerDisplay = document.getElementById('timer');
        timerDisplay.classList.remove('warning');

        this.timer = setInterval(() => {
            this.timeRemaining--;
            timerDisplay.textContent = `${this.timeRemaining}s`;

            if (this.timeRemaining <= 10) {
                timerDisplay.classList.add('warning');
            }

            if (this.timeRemaining <= 0) {
                clearInterval(this.timer);
                // Auto-submit wrong answer
                if (this.selectedAnswer) {
                    this.submitAnswer();
                } else {
                    // Select wrong answer automatically
                    const wrongAnswer = document.querySelector('.answer-btn[data-correct="false"]');
                    if (wrongAnswer) {
                        this.selectAnswer(wrongAnswer);
                        this.submitAnswer();
                    }
                }
            }
        }, 1000);
    }

    showFinalScreen() {
        const accuracy = Math.round((this.correctAnswers / this.questionsAnswered) * 100);

        document.getElementById('final-score').textContent = this.score;
        document.getElementById('final-correct').textContent = `${this.correctAnswers}/${this.questionsAnswered}`;
        document.getElementById('final-accuracy').textContent = `${accuracy}%`;
        document.getElementById('final-streak').textContent = this.bestStreak;

        // Determine mastery level
        let mastery, badge, message;
        if (accuracy >= 90) {
            mastery = 'Master Wizard';
            badge = '🧙‍♂️✨';
            message = 'Incredible! You\'ve mastered the Arcane Auditor rules!';
        } else if (accuracy >= 75) {
            mastery = 'Adept Sorcerer';
            badge = '🔮';
            message = 'Excellent work! You have a strong grasp of the rules.';
        } else if (accuracy >= 60) {
            mastery = 'Apprentice Mage';
            badge = '📚';
            message = 'Good job! Keep practicing to improve your mastery.';
        } else {
            mastery = 'Novice Learner';
            badge = '🎓';
            message = 'Keep learning! Review the rules and try again.';
        }

        document.getElementById('mastery-badge').textContent = badge;
        document.getElementById('mastery-message').textContent = message;

        // Update high score
        if (this.score > this.getHighScore()) {
            this.saveHighScore();
            message += ' 🎊 NEW HIGH SCORE!';
        }

        this.showScreen('final-screen');
    }

    showScreen(screenId) {
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });
        document.getElementById(screenId).classList.add('active');
    }

    backToMenu() {
        clearInterval(this.timer);
        this.showScreen('main-menu');
    }

    updateDashboard() {
        document.getElementById('current-score').textContent = this.score;
        document.getElementById('streak').textContent = this.streak;
        document.getElementById('progress').textContent = `${this.rulesCompleted.size}/42`;
        document.getElementById('high-score').textContent = this.getHighScore();

        // Update streak fire
        const streakFire = document.getElementById('streak-fire');
        if (this.streak >= 5) {
            streakFire.textContent = '🔥🔥🔥';
        } else if (this.streak >= 3) {
            streakFire.textContent = '🔥🔥';
        } else if (this.streak >= 1) {
            streakFire.textContent = '🔥';
        } else {
            streakFire.textContent = '';
        }
    }

    shuffleArray(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }

    getHighScore() {
        return parseInt(localStorage.getItem('arcane-auditor-high-score') || '0');
    }

    saveHighScore() {
        localStorage.setItem('arcane-auditor-high-score', this.score.toString());
    }

    loadHighScore() {
        document.getElementById('high-score').textContent = this.getHighScore();
    }

    // Theme Management
    initializeTheme() {
        // Check for saved theme preference or default to light mode
        const savedTheme = localStorage.getItem('arcane-auditor-game-theme') || 'light';
        this.setTheme(savedTheme);
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        const themeIcon = document.getElementById('theme-icon');
        const themeText = document.getElementById('theme-text');

        if (theme === 'dark') {
            themeIcon.textContent = '☀️';
            themeText.textContent = 'Light Mode';
        } else {
            themeIcon.textContent = '🌙';
            themeText.textContent = 'Dark Mode';
        }

        // Save preference
        localStorage.setItem('arcane-auditor-game-theme', theme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }
}

// Initialize game when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.game = new ArcaneAuditorGame();
});

// Global function for theme toggle (called from HTML onclick)
window.toggleTheme = function() {
    if (window.game) {
        window.game.toggleTheme();
    }
};
