/**
 * Question Navigator Component
 * Manages navigation between questions in a CBT exam
 */

class QuestionNavigator {
    constructor(options = {}) {
        this.container = document.getElementById(options.containerId || 'question-navigator');
        this.currentQuestion = options.currentQuestion || 1;
        this.totalQuestions = options.totalQuestions || 0;
        this.onQuestionChange = options.onQuestionChange || function() {};
        this.questionStates = options.questionStates || {}; // { questionId: 'answered|unanswered|flagged' }
        this.allowNavigation = options.allowNavigation !== false;
        this.oneAtATime = options.oneAtATime === true;
        
        this.render();
        this.attachEventListeners();
    }

    /**
     * Render the question navigator UI
     */
    render() {
        if (!this.container) return;
        
        let html = '<div class="question-navigator">';
        
        // Navigator header
        html += '<div class="navigator-header">';
        html += `<strong>Questions: ${this.currentQuestion}/${this.totalQuestions}</strong>`;
        html += '</div>';
        
        // Navigation buttons
        html += '<div class="navigator-controls">';
        if (this.currentQuestion > 1) {
            html += '<button class="btn btn-sm btn-outline-secondary btn-previous" data-action="previous">';
            html += '<i class="fas fa-chevron-left"></i> Previous';
            html += '</button>';
        }
        if (this.currentQuestion < this.totalQuestions) {
            html += '<button class="btn btn-sm btn-outline-secondary btn-next" data-action="next">';
            html += 'Next <i class="fas fa-chevron-right"></i>';
            html += '</button>';
        }
        html += '</div>';
        
        // Question grid
        if (this.allowNavigation) {
            html += '<div class="navigator-grid">';
            for (let i = 1; i <= this.totalQuestions; i++) {
                const state = this.questionStates[i] || 'unanswered';
                const isCurrent = i === this.currentQuestion;
                const classes = ['question-number', `state-${state}`];
                if (isCurrent) classes.push('active');
                
                html += `<button class="${classes.join(' ')}" data-question="${i}" title="Question ${i}" aria-label="Question ${i} - ${state}">`;
                html += i;
                html += '</button>';
            }
            html += '</div>';
            
            // Legend
            html += '<div class="navigator-legend">';
            html += '<small>';
            html += '<span class="legend-item"><span class="legend-dot answered"></span> Answered</span>';
            html += '<span class="legend-item"><span class="legend-dot unanswered"></span> Unanswered</span>';
            html += '<span class="legend-item"><span class="legend-dot flagged"></span> Flagged</span>';
            html += '</small>';
            html += '</div>';
        }
        
        html += '</div>';
        
        this.container.innerHTML = html;
    }

    /**
     * Attach event listeners to navigator controls
     */
    attachEventListeners() {
        if (!this.container) return;
        
        // Previous/Next buttons
        this.container.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const action = btn.dataset.action;
                if (action === 'previous' && this.currentQuestion > 1) {
                    this.goToQuestion(this.currentQuestion - 1);
                } else if (action === 'next' && this.currentQuestion < this.totalQuestions) {
                    this.goToQuestion(this.currentQuestion + 1);
                }
            });
        });
        
        // Question numbers
        if (this.allowNavigation) {
            this.container.querySelectorAll('.question-number').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    const questionNum = parseInt(btn.dataset.question);
                    this.goToQuestion(questionNum);
                });
            });
        }
    }

    /**
     * Navigate to a specific question
     */
    goToQuestion(questionNum) {
        if (questionNum < 1 || questionNum > this.totalQuestions) return;
        if (questionNum === this.currentQuestion) {
            this.render();
            this.attachEventListeners();
            return;
        }
        this.currentQuestion = questionNum;
        this.onQuestionChange(questionNum);
        this.render();
        this.attachEventListeners();
    }

    setCurrentQuestion(questionNum) {
        if (questionNum < 1 || questionNum > this.totalQuestions) return;
        this.currentQuestion = questionNum;
        this.render();
        this.attachEventListeners();
    }

    /**
     * Update question state (answered/unanswered/flagged)
     */
    updateQuestionState(questionNum, state) {
        this.questionStates[questionNum] = state;
        this.render();
        this.attachEventListeners();
    }

    /**
     * Mark current question as answered
     */
    markCurrentAnswered() {
        this.updateQuestionState(this.currentQuestion, 'answered');
    }

    /**
     * Mark current question as flagged
     */
    markCurrentFlagged() {
        this.updateQuestionState(this.currentQuestion, 'flagged');
    }

    /**
     * Get all question states
     */
    getStates() {
        return this.questionStates;
    }
}

/**
 * Question Timer Component
 * Manages exam countdown timer
 */
class ExamTimer {
    constructor(options = {}) {
        this.container = document.getElementById(options.containerId || 'exam-timer');
        this.totalSeconds = options.totalSeconds || 3600; // 1 hour default
        this.remainingSeconds = this.totalSeconds;
        this.onTimeUp = options.onTimeUp || function() {};
        this.warningThreshold = options.warningThreshold || 300; // 5 minutes
        
        this.running = false;
        this.timerId = null;
        
        this.render();
    }

    /**
     * Start the timer
     */
    start() {
        if (this.running) return;
        this.running = true;
        
        this.timerId = setInterval(() => {
            this.remainingSeconds--;
            this.render();
            
            if (this.remainingSeconds <= 0) {
                this.stop();
                this.onTimeUp();
            }
        }, 1000);
    }

    /**
     * Stop the timer
     */
    stop() {
        if (this.timerId) {
            clearInterval(this.timerId);
            this.timerId = null;
        }
        this.running = false;
    }

    /**
     * Render the timer display
     */
    render() {
        if (!this.container) return;
        
        const minutes = Math.floor(this.remainingSeconds / 60);
        const seconds = this.remainingSeconds % 60;
        const display = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        
        let alertClass = '';
        if (this.remainingSeconds <= this.warningThreshold && this.remainingSeconds > 60) {
            alertClass = 'alert-warning';
        } else if (this.remainingSeconds <= 60) {
            alertClass = 'alert-danger';
        }
        
        let html = `<div class="exam-timer ${alertClass}">`;
        html += `<i class="fas fa-hourglass-end"></i> ${display}`;
        html += '</div>';
        
        this.container.innerHTML = html;
    }

    /**
     * Add seconds to the timer
     */
    addTime(seconds) {
        this.remainingSeconds += seconds;
        this.render();
    }

    /**
     * Get remaining time in seconds
     */
    getRemainingTime() {
        return this.remainingSeconds;
    }
}

/**
 * Question Flag Manager
 * Manages flagged questions for review
 */
class FlagManager {
    constructor(options = {}) {
        this.container = document.getElementById(options.containerId || 'flagged-container');
        this.flaggedQuestions = options.flaggedQuestions || [];
        this.onFlaggedClick = options.onFlaggedClick || function() {};
        
        this.render();
    }

    /**
     * Toggle flag status for a question
     */
    toggleFlag(questionNum) {
        const index = this.flaggedQuestions.indexOf(questionNum);
        if (index > -1) {
            this.flaggedQuestions.splice(index, 1);
        } else {
            this.flaggedQuestions.push(questionNum);
        }
        this.render();
    }

    /**
     * Check if a question is flagged
     */
    isFlagged(questionNum) {
        return this.flaggedQuestions.includes(questionNum);
    }

    /**
     * Get all flagged questions
     */
    getFlagged() {
        return this.flaggedQuestions;
    }

    /**
     * Render the flagged questions list
     */
    render() {
        if (!this.container || this.flaggedQuestions.length === 0) return;
        
        let html = '<div class="flagged-questions">';
        html += '<h6 class="mb-2"><i class="fas fa-flag"></i> Flagged for Review</h6>';
        html += '<div class="flagged-list">';
        
        this.flaggedQuestions.forEach(qNum => {
            html += `<button class="flagged-item" data-question="${qNum}">Q${qNum}</button>`;
        });
        
        html += '</div>';
        html += '</div>';
        
        this.container.innerHTML = html;
        this.attachEventListeners();
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        if (this.container) {
            this.container.querySelectorAll('.flagged-item').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    const qNum = parseInt(btn.dataset.question);
                    this.onFlaggedClick(qNum);
                });
            });
        }
    }
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { QuestionNavigator, ExamTimer, FlagManager };
}
