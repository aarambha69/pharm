const { machineIdSync } = require('node-machine-id');

const getMachineId = () => {
    try {
        return machineIdSync();
    } catch (err) {
        console.error('Error getting machine ID:', err);
        return 'UNKNOWN_MACHINE';
    }
};

// Simple license key validation logic
// In a real app, this would be more complex (signing/encryption)
const validateLicense = (clientMachineId, licenseKey) => {
    // For demonstration, let's say a valid key is just base64(machineId + secret)
    const expected = Buffer.from(clientMachineId + 'AARAMBHA_SECRET').toString('base64');
    return licenseKey === expected;
};

module.exports = { getMachineId, validateLicense };
