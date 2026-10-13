(() => {
  const toggle = document.getElementById('globalCalculatorToggle');
  const calculator = document.getElementById('siteCalculator');
  if (!toggle || !calculator) return;

  const mode = calculator.dataset.calculatorMode === 'simple' ? 'simple' : 'full';
  const expressionOutput = document.getElementById('siteCalculatorExpression');
  const valueOutput = document.getElementById('siteCalculatorValue');
  const modeOutput = document.getElementById('siteCalculatorMode');
  const closeButton = document.getElementById('siteCalculatorClose');
  const keys = document.getElementById('siteCalculatorKeys');
  const fullFunctions = ['sin(', 'cos(', 'tan(', 'sqrt(', 'log(', 'ln(', 'abs('];
  let expression = '';
  let result = 0;
  let evaluated = false;
  let hasError = false;

  if (mode === 'simple') {
    keys.querySelectorAll('[data-simple-position]').forEach((button) => {
      const [row, column] = button.dataset.simplePosition.split('-');
      button.style.gridRow = row;
      button.style.gridColumn = column;
    });
  }

  modeOutput.textContent = mode === 'simple' ? 'Simple mode' : 'Full mode';

  function render() {
    expressionOutput.textContent = expression || (evaluated ? '=' : '\u00a0');
    valueOutput.textContent = hasError
      ? 'Invalid expression'
      : new Intl.NumberFormat(undefined, { maximumFractionDigits: 10 }).format(result);
    calculator.classList.toggle('site-calculator-error', hasError);
  }

  function append(value) {
    if (hasError) clear();
    if (evaluated) {
      if (/^[0-9.]$/.test(value) || /^[a-z(]/i.test(value)) {
        expression = '';
      } else {
        expression = String(result);
      }
      evaluated = false;
    }
    expression = (expression + value).slice(0, 180);
    render();
  }

  function clear() {
    expression = '';
    result = 0;
    evaluated = false;
    hasError = false;
    render();
  }

  function backspace() {
    if (hasError || evaluated) {
      clear();
      return;
    }
    const functionToken = fullFunctions.find((token) => expression.endsWith(token));
    if (functionToken) {
      expression = expression.slice(0, -functionToken.length);
    } else if (expression.endsWith('pi')) {
      expression = expression.slice(0, -2);
    } else {
      expression = expression.slice(0, -1);
    }
    render();
  }

  function evaluateExpression(source) {
    const normalized = source
      .replace(/\u03c0/g, 'pi')
      .replace(/\u00d7/g, '*')
      .replace(/\u00f7/g, '/')
      .replace(/\u2212/g, '-')
      .replace(/\s+/g, '')
      .toLowerCase();
    const tokenizer = /(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?|[a-z]+|[()+\-*/^%]/gy;
    const tokens = [];
    let cursor = 0;
    while (cursor < normalized.length) {
      tokenizer.lastIndex = cursor;
      const match = tokenizer.exec(normalized);
      if (!match) throw new Error('Invalid character');
      tokens.push(match[0]);
      cursor = tokenizer.lastIndex;
    }

    let index = 0;
    const peek = () => tokens[index];
    const take = () => tokens[index++];
    const expect = (token) => {
      if (take() !== token) throw new Error('Missing bracket');
    };

    function parseExpression() {
      let value = parseTerm();
      while (peek() === '+' || peek() === '-') {
        const operator = take();
        const right = parseTerm();
        value = operator === '+' ? value + right : value - right;
      }
      return value;
    }

    function parseTerm() {
      let value = parseUnary();
      while (peek() === '*' || peek() === '/') {
        const operator = take();
        const right = parseUnary();
        value = operator === '*' ? value * right : value / right;
      }
      return value;
    }

    function parseUnary() {
      if (peek() === '+') {
        take();
        return parseUnary();
      }
      if (peek() === '-') {
        take();
        return -parseUnary();
      }
      return parsePower();
    }

    function parsePower() {
      let value = parsePrimary();
      if (peek() === '^') {
        if (mode !== 'full') throw new Error('Power is unavailable in simple mode');
        take();
        value = Math.pow(value, parseUnary());
      }
      return value;
    }

    function parsePrimary() {
      const token = take();
      let value;
      if (token === '(') {
        value = parseExpression();
        expect(')');
      } else if (token && /^\d/.test(token) || token && /^\.\d/.test(token)) {
        value = Number(token);
      } else if (token === 'pi') {
        if (mode !== 'full') throw new Error('Constants are unavailable in simple mode');
        value = Math.PI;
      } else if (token === 'e') {
        if (mode !== 'full') throw new Error('Constants are unavailable in simple mode');
        value = Math.E;
      } else if (['sin', 'cos', 'tan', 'sqrt', 'log', 'ln', 'abs'].includes(token)) {
        if (mode !== 'full') throw new Error('Functions are unavailable in simple mode');
        expect('(');
        const argument = parseExpression();
        expect(')');
        if (token === 'sin') value = Math.sin(argument * Math.PI / 180);
        if (token === 'cos') value = Math.cos(argument * Math.PI / 180);
        if (token === 'tan') value = Math.tan(argument * Math.PI / 180);
        if (token === 'sqrt') value = Math.sqrt(argument);
        if (token === 'log') value = Math.log10(argument);
        if (token === 'ln') value = Math.log(argument);
        if (token === 'abs') value = Math.abs(argument);
      } else {
        throw new Error('Incomplete expression');
      }

      while (peek() === '%') {
        if (mode !== 'full') throw new Error('Percent is unavailable in simple mode');
        take();
        value /= 100;
      }
      return value;
    }

    if (!tokens.length) return 0;
    const value = parseExpression();
    if (index !== tokens.length || !Number.isFinite(value)) throw new Error('Invalid result');
    return Number(value.toPrecision(12));
  }

  function calculate() {
    if (!expression) return;
    try {
      result = evaluateExpression(expression);
      evaluated = true;
      hasError = false;
      expressionOutput.textContent = `${expression} =`;
      valueOutput.textContent = new Intl.NumberFormat(undefined, { maximumFractionDigits: 10 }).format(result);
      calculator.classList.remove('site-calculator-error');
    } catch (error) {
      hasError = true;
      render();
    }
  }

  function setOpen(isOpen) {
    calculator.hidden = !isOpen;
    toggle.setAttribute('aria-expanded', String(isOpen));
    toggle.setAttribute('aria-label', isOpen ? 'Close calculator' : 'Open calculator');
    if (isOpen) document.getElementById('siteCalculatorDisplay').focus();
  }

  toggle.addEventListener('click', () => setOpen(calculator.hidden));
  closeButton.addEventListener('click', () => setOpen(false));
  keys.addEventListener('click', (event) => {
    const button = event.target.closest('button');
    if (!button) return;
    const action = button.dataset.calculatorAction;
    if (action === 'clear') clear();
    else if (action === 'backspace') backspace();
    else if (action === 'equals') calculate();
    else if (button.dataset.calculatorValue) append(button.dataset.calculatorValue);
  });

  calculator.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      event.preventDefault();
      setOpen(false);
    } else if (event.key === 'Enter' || event.key === '=') {
      event.preventDefault();
      calculate();
    } else if (event.key === 'Backspace') {
      event.preventDefault();
      backspace();
    } else if (/^[0-9.+\-*/%^()]$/.test(event.key)) {
      if (mode === 'simple' && '()%^'.includes(event.key)) return;
      event.preventDefault();
      append(event.key);
    }
  });

  document.addEventListener('click', (event) => {
    if (!calculator.hidden && !calculator.contains(event.target) && !toggle.contains(event.target)) setOpen(false);
  });
  render();
})();
