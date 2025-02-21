/**
 * Delays execution for a specified amount of time and then resolves a Promise with a given count.
 * 
 * Why this exists:
 * - To simulate delay in execution or to mimic asynchronous operations.
 * - Useful for testing and demonstration of async/await syntax.
 * 
 * @param milliseconds - The amount of delay in milliseconds. 
 *    Example: 500
 * @param count - The number to be returned after the delay.
 *    Example: 5
 * 
 * @returns A Promise that resolves with the provided count after the specified delay.
 *    Example: Promise that resolves to 5 after 500 milliseconds.
 * 
 * @example
 * // Basic usage
 * const result = await delay(500, 5);
 * console.log(result); // Logs "5" after 500 milliseconds.
 */
function delay(milliseconds: number, count: number): Promise<number> {
    return new Promise<number>(resolve => {
            setTimeout(() => {
                resolve(count);
            }, milliseconds);
        });
}

/**
 * Prints a dramatic welcome message with a delay between each part.
 * 
 * Why this exists:
 * - Demonstrates the use of async/await syntax with Promises.
 * - Provides a fun, interactive way to understand asynchronous operations.
 * 
 * @returns A Promise that resolves when the entire message has been logged.
 *    Example: Promise that resolves after "Hello", 0 to 4, and "World!" have been logged with delays.
 * 
 * @example
 * // Basic usage
 * await dramaticWelcome();
 * // Logs "Hello", 0 to 4, and "World!" with a delay of 500 milliseconds between each log.
 * 
 * @see delay - Used internally to create delay between logs.
 */
async function dramaticWelcome(): Promise<void> {
    console.log("Hello");

    for (let i = 0; i < 5; i++) {
        const count: number = await delay(500, i);
        console.log(count);
    }

    console.log("World!");
}

dramaticWelcome();