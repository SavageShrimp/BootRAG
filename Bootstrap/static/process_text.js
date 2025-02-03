class StringProcessor {
  constructor() {
    this.resetStringProcessor();
  }

  resetStringProcessor() {
    /** Internal string member */
    this.memberString = '';
    /** String list member */
    this.stringList = [];
    /** Flag variable */
    this.inCode = false;
    /** String language name */
    this.languageName = '';
    /** Flag to track code match */
    this.codeMatched = false;
    /** Flag to track text match */
    this.textMatched = false;
    this.regexMatched = false
    this.Streaming = false
  }

  /**
   * Appends a passed string argument to memberString
   * @param {string} stringToAdd - The string to append
   */
  appendString(stringToAdd) {
    this.memberString += stringToAdd;
  }

  /**
   * Checks and processes the memberString when inCode is false
   */
  detectCodeAndSwitch() {
    console.log("detectCodeAndSwitch");
    if (!this.inCode) {
      const codeMatch = this.memberString.match(/```(\w+?)\b\s+/);
      if (codeMatch) {
        this.regexMatched = true
        console.log("start of code tag match");
        console.log(this.memberString)
        this.inCode = true;
        this.languageName = codeMatch[1];
        const remainingString = this.memberString.slice(0, codeMatch.index);
        console.log(this.remainingString)
        const obj = {
          type: 'text',
          text: remainingString,
        };
        this.stringList.push(obj);
        // Set memberString to the remaining string after the match
        this.memberString = this.memberString.slice(codeMatch.index + codeMatch[0].length);
      } else {
        console.log("code tag not matched ");
      }
    }
  }

  /**
   * Checks and processes the memberString when inCode is true
   */
 detectTextAndSwitch() {
  console.log("detectTextAndSwitch");
  if (this.inCode) {
    const textMatch = this.memberString.match(/```\s+/);
    if (textMatch) {
      this.regexMatched = true
      this.inCode = false;
      console.log("end of code tag match");
      this.languageName = 'none';
      // Remove the matched string from the end of memberString
      const remainingString = this.memberString.slice(0, textMatch.index);
      // Create an object and add it to stringList
      const obj = {
        type: 'code',
        text: remainingString,
      };
      this.stringList.push(obj);
      // Set memberString to the remaining string after the match
      this.memberString = this.memberString.slice(textMatch.index + textMatch[0].length);
    }
  }
}

  /**
   * Returns '&' concatenated with the provided string
   * @param {string} str - The string to process
   * @returns {string} The concatenated string
   */
  generateElementString(str) {
    return '&' + str;
  }

  /**
   * Replaces characters with their corresponding HTML entities and applies the '&' prefix
   * @param {string} str - The string to process
   * @returns {string} The processed string
   */
  mapHTMLElements(str) {
    return str.replace(/&|<|>|\"|'/g, (match) => {
      switch (match) {
        case '&':
          return this.generateElementString('amp;');
        case '<':
          return this.generateElementString('lt;');
        case '>':
          return this.generateElementString('gt;');
        case '"':
          return this.generateElementString('quot;');
        case "'":
          return this.generateElementString('apos;');
        default:
          return this.generateElementString(match);
      }
    });
  }

  /**
   * Updates the state by calling the appropriate method based on inCode
   */
  updateState() {
    this.regexMatched = false
    if (this.inCode) {
      this.detectTextAndSwitch();
    } else {
      this.detectCodeAndSwitch();
    }
  }

  isMemberStringNotEmpty() {
    return this.memberString !== '';
  }

    processText(str)
    {
        this.appendString(str)
        this.updateState()

        while (this.regexMatched == true)
        {
            this.updateState()
        }
    }

  /**
   * Builds a string from the stringList and the memberString, formatting code and text items appropriately
   * @returns {string} The formatted string
   */
  getText() {
    let result = '';

    // First process the stringList
    for (const item of this.stringList) {
      if (item.type === 'code') {
        console.log("generate code block")
        result += `<pre><code class='language-${this.languageName}'>${this.mapHTMLElements(item.text)}</code></pre>`;
      } else {
        const textWithBr = item.text.replace(/\n/g, '<br>');
        result += textWithBr;
      }
    }

    // Then process the memberString based on inCode
    if (this.inCode) {
        console.log("generate text block")
      result += `<pre><code class='language-${this.languageName}'>${this.mapHTMLElements(this.memberString)}</code></pre>`;
    } else {
      result += this.memberString.replace(/\n/g, '<br>');
    }

//    if (false == this.regexMatched)
//    {
//       this.memberString = ''
//    }

    return result;
  }
}
