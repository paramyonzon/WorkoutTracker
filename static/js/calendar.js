document.addEventListener('DOMContentLoaded', function() {
    const calendarContainer = document.getElementById('workoutCalendar');
    let workoutData = {};

    function createCalendar(data) {
        const today = new Date();
        const endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        const startDate = new Date(endDate);
        startDate.setMonth(startDate.getMonth() - 11);
        startDate.setDate(1);

        // Ensure startDate is a Monday
        while (startDate.getDay() !== 1) {
            startDate.setDate(startDate.getDate() - 1);
        }

        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const days = ['Mon', 'Wed', 'Fri'];

        let html = '<div class="calendar-wrapper">';
        
        // Add month labels
        html += '<div class="month-labels">';
        let currentMonth = new Date(startDate);
        while (currentMonth <= endDate) {
            if (currentMonth.getDate() === 1) {
                const monthIndex = currentMonth.getMonth();
                html += `<div class="month-label" style="grid-column-start: ${Math.floor((currentMonth - startDate) / (24 * 60 * 60 * 1000) / 7) + 1}">${months[monthIndex]}</div>`;
            }
            currentMonth.setDate(currentMonth.getDate() + 1);
        }
        html += '</div>';

        // Add day labels and calendar grid
        html += '<div class="calendar-content">';
        html += '<div class="day-labels">';
        days.forEach((day, index) => {
            html += `<div class="day-label" style="grid-row: ${index * 2 + 1} / span 2;">${day}</div>`;
        });
        html += '</div>';

        // Add calendar squares
        html += '<div class="calendar-grid">';
        let currentDate = new Date(startDate);
        let weekCount = 0;
        
        while (currentDate <= endDate) {
            const dateString = currentDate.toISOString().split('T')[0];
            const duration = data[dateString] || 0;
            const intensity = getIntensity(duration);
            html += `<div class="calendar-day intensity-${intensity}" data-date="${dateString}" data-duration="${duration}" style="grid-row: ${(currentDate.getDay() - 1) % 7 + 1}; grid-column: ${weekCount + 1};"></div>`;
            
            if (currentDate.getDay() === 0) {
                weekCount++;
            }
            
            currentDate.setDate(currentDate.getDate() + 1);
        }
        html += '</div>';
        html += '</div>';

        // Add legend
        html += `
        <div class="calendar-legend">
            <span>Less</span>
            <div class="legend-item intensity-0"></div>
            <div class="legend-item intensity-1"></div>
            <div class="legend-item intensity-2"></div>
            <div class="legend-item intensity-3"></div>
            <div class="legend-item intensity-4"></div>
            <span>More</span>
        </div>`;

        html += '</div>';
        calendarContainer.innerHTML = html;

        // Add tooltip functionality
        const tooltip = document.createElement('div');
        tooltip.className = 'calendar-tooltip';
        document.body.appendChild(tooltip);

        calendarContainer.addEventListener('mouseover', function(e) {
            if (e.target.classList.contains('calendar-day')) {
                const date = new Date(e.target.dataset.date);
                const duration = e.target.dataset.duration;
                tooltip.innerHTML = `${date.toDateString()}<br>Duration: ${duration} minutes`;
                tooltip.style.display = 'block';
                tooltip.style.left = `${e.pageX + 10}px`;
                tooltip.style.top = `${e.pageY + 10}px`;
            }
        });

        calendarContainer.addEventListener('mouseout', function(e) {
            if (e.target.classList.contains('calendar-day')) {
                tooltip.style.display = 'none';
            }
        });
    }

    function getIntensity(duration) {
        if (duration === 0) return 0;
        if (duration <= 15) return 1;
        if (duration <= 30) return 2;
        if (duration <= 60) return 3;
        return 4;
    }

    function fetchWorkouts() {
        fetch('/api/workouts')
            .then(response => response.json())
            .then(data => {
                workoutData = data.reduce((acc, workout) => {
                    acc[workout.date] = (acc[workout.date] || 0) + workout.duration;
                    return acc;
                }, {});
                createCalendar(workoutData);
            });
    }

    function fetchStats() {
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                document.getElementById('totalWorkouts').textContent = data.total_workouts;
                document.getElementById('currentStreak').textContent = data.current_streak;
                document.getElementById('mostActiveDay').textContent = data.most_active_day ? new Date(data.most_active_day).toDateString() : 'N/A';
            });
    }

    document.getElementById('addWorkoutForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const date = document.getElementById('date').value;
        const duration = parseInt(document.getElementById('duration').value);
        const exerciseType = document.getElementById('exerciseType').value;

        fetch('/api/add_workout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ date, duration, exercise_type: exerciseType }),
        })
        .then(response => response.json())
        .then(data => {
            workoutData[data.date] = (workoutData[data.date] || 0) + data.duration;
            createCalendar(workoutData);
            fetchStats();
            e.target.reset();
        });
    });

    fetchWorkouts();
    fetchStats();
});
