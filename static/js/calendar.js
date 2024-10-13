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

        // Add event listeners for mouseover and click
        calendarDay.addEventListener('mouseover', () => showActivityDetails(dateString, calendarDay));
        calendarDay.addEventListener('click', () => showActivityDetails(dateString, calendarDay, true));

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

function showActivityDetails(date, element, isPermanent = false) {
    // Remove existing tooltips
    const existingTooltip = document.querySelector('.activity-tooltip');
    if (existingTooltip) {
        existingTooltip.remove();
    }

    // Fetch activity details
    fetch(`/activity_details/${date}`)
        .then(response => response.json())
        .then(data => {
            const tooltip = document.createElement('div');
            tooltip.classList.add('activity-tooltip');
            tooltip.innerHTML = `
                <strong>Date:</strong> ${date}<br>
                <strong>Activity Level:</strong> ${(data.activity_level * 100).toFixed(2)}%<br>
                <strong>Activities:</strong> ${data.activities.join(', ')}
            `;

            // Position the tooltip
            const rect = element.getBoundingClientRect();
            tooltip.style.position = 'absolute';
            tooltip.style.top = `${rect.bottom + window.scrollY}px`;
            tooltip.style.left = `${rect.left + window.scrollX}px`;
            tooltip.style.zIndex = '1000';
            tooltip.style.backgroundColor = 'var(--bs-dark)';
            tooltip.style.color = 'var(--bs-light)';
            tooltip.style.padding = '10px';
            tooltip.style.borderRadius = '5px';
            tooltip.style.boxShadow = '0 2px 5px rgba(0, 0, 0, 0.2)';

            document.body.appendChild(tooltip);

            if (!isPermanent) {
                element.addEventListener('mouseout', () => tooltip.remove());
            } else {
                tooltip.style.cursor = 'pointer';
                tooltip.addEventListener('click', (e) => {
                    e.stopPropagation();
                    tooltip.remove();
                });
            }
        })
        .catch(error => console.error('Error fetching activity details:', error));
}
