// Failing test script for browser context
// This test is designed to fail to show retry logic and artifact capture

// This will fail - trying to access a property of null
const nonExistentElement = document.querySelector('#this-element-does-not-exist');
const text = nonExistentElement.textContent; // This will throw an error

// This line should never be reached
console.log('This should not be reached'); 