document.addEventListener('DOMContentLoaded', function() {
    const mapDiv = document.getElementById('choropleth-map');
    const layout = {
        geo: {
            scope: 'europe',
            showframe: true,
            showcoastlines: false,
            projection: {
                type: 'mercator'
            }
        },
        title: 'UK Parliamentary Constituencies'
    };

    const initialData = [{
        type: 'choropleth',
        locationmode: 'country names',
        locations: ['England', 'Scotland', 'Wales'],  
        z: [1, 2, 3],  
        text: ['England', 'Scotland', 'Wales'], 
        autocolorscale: true
    }];    

    // Function to update the map with fetched data
    function updateMap(dataType) {
        const url = `/choropleth/data?type=${dataType}`;
        fetch(url)
            .then(response => response.json())
            .then(data => {
                // Update the map with fetched data
                Plotly.react(mapDiv, data, layout);
            })
            .catch(error => console.error('Error fetching data:', error));
    }

    // Call updateMap function initially with a default data type
    updateMap('vote'); 
});


