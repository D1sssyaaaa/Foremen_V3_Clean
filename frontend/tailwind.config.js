/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                red: {
                    1200: '#2a0a0a', // Custom ultra-dark red
                }
            }
        },
    },
    plugins: [],
}
