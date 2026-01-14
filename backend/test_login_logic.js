const bcrypt = require('bcrypt');

async function test() {
    const inputPass = "123456";
    const storedPass = "123456";

    console.log(`Input: ${inputPass}, Stored: ${storedPass}`);

    try {
        const isMatch = await bcrypt.compare(inputPass, storedPass);
        console.log("Bcrypt compare result:", isMatch);
        if (isMatch) {
            console.log("MATCH via bcrypt");
        } else {
            console.log("NO MATCH via bcrypt. Checking plain text...");
            if (inputPass === storedPass) {
                console.log("MATCH via plain text fallback");
            } else {
                console.log("NO MATCH via plain text either");
            }
        }
    } catch (e) {
        console.log("Bcrypt threw error:", e.message);
        if (inputPass === storedPass) {
            console.log("MATCH via catch block plain text check");
        } else {
            console.log("NO MATCH via catch block");
        }
    }
}

test();
