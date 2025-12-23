document.addEventListener("DOMContentLoaded", () => {
    const yCtx = document.getElementById('yAxisChart').getContext('2d');
    const ctx = document.getElementById('weatherChart').getContext('2d');
    if (!ctx || !window.weather) return;

    const canvas = document.getElementById('weatherChart');
    const styles = getComputedStyle(canvas);

    const dataset = [{
            label: 'Temperature (°F)',
            data: window.weather.hourly.temp,
            borderColor: styles.getPropertyValue('--temperature-color'),
            backgroundColor: styles.getPropertyValue('--temperature-color'),
            fill: true,
            yAxisID: 'yTemp',
            tension: 0.4
        },
        {
            label: 'Precipitation (In.)',
            data: window.weather.hourly.precipitation,
            borderColor: styles.getPropertyValue('--precipitation-color'),
            backgroundColor: styles.getPropertyValue('--precipitation-color'),
            fill: true,
            yAxisID: 'yPrecip',
            tension: 0.4
        },
        {
            label: 'Cloud Cover',
            data: window.weather.hourly.cloud_cover,
            borderColor: styles.getPropertyValue('--cloud-cover-color'),
            backgroundColor: styles.getPropertyValue('--cloud-cover-color'),
            fill: true,
            yAxisID: 'yPercent',
            tension: 0.4
        },
        {
            label: 'Precipitation %',
            data: window.weather.hourly.precipitation_probability,
            borderColor: styles.getPropertyValue('--precipitation-percent-color'),
            backgroundColor: styles.getPropertyValue('--precipitation-percent-color'),
            fill: true,
            yAxisID: 'yPercent',
            tension: 0.4,
        }]

    const data = {
        labels: window.weather.hourly.time,
        datasets: dataset
    };

    const config = {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                    position: 'bottom',
                    align: 'start',
                    labels: {
                        color: '#E1E2E0'
                    }
                },
                title: {
                    display: false,
                    text: 'System Temperature Over Time'
                }
            },
            scales: {
                x: {
                    grid:{
                        color: 'rgba(225, 226, 224, .75)'
                    },
                    ticks: {
                        color: '#E1E2E0',
                        autoSkip: false
                    },
                    title: {
                        display: true,
                        text: 'Timestamp',
                        color: '#E1E2E0'
                    }
                },
                y: {
                    display: false, 
                    labels: {
                        display: false,
                        color: 'rgba(225, 226, 224, 0)'
                    },
                    grid:{
                        color: 'rgba(225, 226, 224, .75)',
                        display: true
                    },
                },
                yTemp: {
                    display: false
                },
                yPrecip: {
                    display: false
                },
                yPercent: {
                    display: false
                }
            }
        }
    };

    const yAxisChart = new Chart(yCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                {
                    label: dataset[0].label, 
                    backgroundColor: styles.getPropertyValue('--temperature-color')
                },
                {
                    label: dataset[1].label, 
                    backgroundColor: styles.getPropertyValue('--precipitation-color')
                },
                {    
                    label: dataset[2].label, 
                    backgroundColor: styles.getPropertyValue('--cloud-cover-color')
                },
                {
                    label: dataset[3].label, 
                    backgroundColor: styles.getPropertyValue('--precipitation-percent-color')
                },
            ]},
            options: {
                responsive: false,
                plugins: { 
                    legend: {
                        display: true,
                        position: 'left',
                        // align: 'bottom',
                        labels: {
                            color: '#E1E2E0',
                            boxWidth: 12,
                            padding: 8
                        }
                    },
                scales: {
                    x: { display: false },
                    yTemp: {
                        display: true,
                        grid:{
                            color: 'rgba(225, 226, 224, .75)'
                        },
                        ticks: {
                            color: styles.getPropertyValue('--temperature-color')
                        },
                        title: {
                            display: true,
                            text: 'Temperature (°F)',
                            color: styles.getPropertyValue('--temperature-color')
                        }
                    },
                    yPrecip: {
                        type: 'linear',
                        position: 'left',
                        min: 0,
                        grid:{
                            drawOnChartArea: false
                        },
                        ticks: {
                            color: styles.getPropertyValue('--precipitation-color')
                        },
                        title: {
                            display: true,
                            text: 'Precipitation (In)',
                            color: styles.getPropertyValue('--precipitation-color')
                        }
                    },
                    yPercent: {
                        type: 'linear',
                        position: 'left',
                        min: 0,
                        max: 100,
                        grid:{
                            drawOnChartArea: false
                        },
                        ticks: {
                            color: '#E1E2E0'
                        },
                        title: {
                            display: true,
                            text: '% Chance',
                            color: '#E1E2E0'
                        }
                    }
                }
            }
        }
    });
    const tempChart = new Chart(ctx, config);
});