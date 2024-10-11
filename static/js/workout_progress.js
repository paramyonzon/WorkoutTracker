document.addEventListener('DOMContentLoaded', function() {
    const progressCtx = document.getElementById('workoutProgressChart').getContext('2d');
    const weeklyCtx = document.getElementById('weeklyWorkoutChart').getContext('2d');
    const exerciseTypeCtx = document.getElementById('exerciseTypeChart').getContext('2d');
    let progressChart, weeklyChart, exerciseTypeChart;

    function fetchWorkoutProgress() {
        fetch('/api/workout_progress')
            .then(response => response.json())
            .then(data => {
                const labels = data.map(item => item.date);
                const totalDurations = data.map(item => item.total_duration);

                if (progressChart) {
                    progressChart.destroy();
                }

                progressChart = new Chart(progressCtx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Total Workout Duration (minutes)',
                            data: totalDurations,
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            x: {
                                type: 'time',
                                time: {
                                    unit: 'day'
                                },
                                title: {
                                    display: true,
                                    text: 'Date'
                                }
                            },
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Total Duration (minutes)'
                                }
                            }
                        }
                    }
                });
            });
    }

    function fetchWeeklyWorkouts() {
        fetch('/api/weekly_workouts')
            .then(response => response.json())
            .then(data => {
                const labels = data.map(item => item.week);
                const durations = data.map(item => item.total_duration);

                if (weeklyChart) {
                    weeklyChart.destroy();
                }

                weeklyChart = new Chart(weeklyCtx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Weekly Workout Duration (minutes)',
                            data: durations,
                            backgroundColor: 'rgba(75, 192, 192, 0.6)',
                            borderColor: 'rgb(75, 192, 192)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Duration (minutes)'
                                }
                            }
                        }
                    }
                });
            });
    }

    function fetchExerciseTypeDistribution() {
        fetch('/api/exercise_type_distribution')
            .then(response => response.json())
            .then(data => {
                const labels = Object.keys(data);
                const values = Object.values(data);

                if (exerciseTypeChart) {
                    exerciseTypeChart.destroy();
                }

                exerciseTypeChart = new Chart(exerciseTypeCtx, {
                    type: 'pie',
                    data: {
                        labels: labels,
                        datasets: [{
                            data: values,
                            backgroundColor: [
                                'rgba(255, 99, 132, 0.8)',
                                'rgba(54, 162, 235, 0.8)',
                                'rgba(255, 206, 86, 0.8)',
                                'rgba(75, 192, 192, 0.8)',
                                'rgba(153, 102, 255, 0.8)'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'top',
                            },
                            title: {
                                display: true,
                                text: 'Exercise Type Distribution'
                            }
                        }
                    }
                });
            });
    }

    fetchWorkoutProgress();
    fetchWeeklyWorkouts();
    fetchExerciseTypeDistribution();

    document.getElementById('addWorkoutForm').addEventListener('submit', function(e) {
        e.preventDefault();
        // ... (existing code for adding a workout)
        .then(() => {
            fetchWorkoutProgress();
            fetchWeeklyWorkouts();
            fetchExerciseTypeDistribution();
        });
    });
});