const xlsx = require('xlsx');
const path = require('path');

// Create sample Excel file for SMS bulk upload
const sampleData = [
    { phone: '9855062769', name: 'John Doe' },
    { phone: '9800000000', name: 'Jane Smith' },
    { phone: '9841234567', name: 'Bob Johnson' },
    { phone: '9812345678', name: 'Alice Williams' },
    { phone: '9823456789', name: 'Charlie Brown' }
];

const worksheet = xlsx.utils.json_to_sheet(sampleData);
const workbook = xlsx.utils.book_new();
xlsx.utils.book_append_sheet(workbook, worksheet, 'Contacts');

// Add column widths
worksheet['!cols'] = [
    { wch: 15 },  // phone column
    { wch: 20 }   // name column
];

// Save the file
const outputPath = path.join(__dirname, 'uploads', 'SMS_Template.xlsx');
xlsx.writeFile(workbook, outputPath);

console.log('✅ Sample SMS template created:', outputPath);
