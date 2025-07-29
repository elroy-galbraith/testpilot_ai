// Sample test script for browser context
// This test is designed to pass to show successful execution

async function runSampleTest() {
    try {
        // Verify we're in a browser environment
        if (typeof window === 'undefined') {
            throw new Error('Not in browser environment');
        }
        
        // Verify document is available
        if (typeof document === 'undefined') {
            throw new Error('Document not available');
        }
        
        // Create a test element and verify DOM manipulation works
        const testDiv = document.createElement('div');
        testDiv.id = 'test-element';
        testDiv.textContent = 'Test content';
        document.body.appendChild(testDiv);
        
        // Verify the element was created
        const foundElement = document.getElementById('test-element');
        if (!foundElement) {
            throw new Error('Test element not found after creation');
        }
        
        // Verify text content
        if (foundElement.textContent !== 'Test content') {
            throw new Error('Test element text content mismatch');
        }
        
        // Clean up
        document.body.removeChild(testDiv);
        
        // Log success
        console.log('✅ Test passed successfully!');
        console.log('DOM manipulation working correctly');
        
    } catch (error) {
        console.error('Test failed:', error.message);
        throw error;
    }
}

// Execute the sample test
runSampleTest(); 