function renderCalendar(activityData) {
    const calendarElement = document.getElementById('calendar');
    const today = new Date();
    const currentYear = today.getFullYear();
    const currentMonth = today.getMonth();

    // Clear existing calendar
    calendarElement.innerHTML = '';

    // Add day labels
    const dayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    dayLabels.forEach(day => {
        const dayLabel = document.createElement('div');
        dayLabel.textContent = day;
        dayLabel.classList.add('calendar-day', 'fw-bold');
        calendarElement.appendChild(dayLabel);
    });

    // Get the first day of the month
    const firstDay = new Date(currentYear, currentMonth, 1);
    const startingDay = firstDay.getDay();

    // Add empty cells for days before the first day of the month
    for (let i = 0; i < startingDay; i++) {
        const emptyDay = document.createElement('div');
        emptyDay.classList.add('calendar-day');
        calendarElement.appendChild(emptyDay);
    }

    // Get the number of days in the current month
    const lastDay = new Date(currentYear, currentMonth + 1, 0);
    const daysInMonth = lastDay.getDate();

    // Add calendar days
    for (let day = 1; day <= daysInMonth; day++) {
        const calendarDay = document.createElement('div');
        calendarDay.textContent = day;
        calendarDay.classList.add('calendar-day');

        const currentDate = new Date(currentYear, currentMonth, day);
        const dateString = currentDate.toISOString().split('T')[0];
        const activityLevel = activityData[dateString] || 0;

        // Set background color based on activity level
        const bgColor = getColorForActivityLevel(activityLevel);
        calendarDay.style.backgroundColor = bgColor;

        calendarElement.appendChild(calendarDay);
    }
}

function getColorForActivityLevel(level) {
    // Convert activity level (0-1) to a color scale from light green to dark green
    const r = Math.round(230 - (level * 230));
    const g = 255;
    const b = Math.round(230 - (level * 230));
    return `rgb(${r}, ${g}, ${b})`;
}
