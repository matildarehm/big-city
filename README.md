# big-city
NYC Geocode API

*An npm package for geocoded searching and reverse searching addresses or endpoints within New York City*

### schemas

**borough schema**
```javascript
"manhattan": [
    {
      "neighborhood": "Little Italy"
      "zipCodes": [ 10012, 10013 ]
    },
    {
      "neighborhood": "Financial District"
      "zipCodes": [ 10004, 10005, 10006, 10038 ]
    }
]

```

**neighborhood schema**
```javascript
{
  "neighborhood": "Financial District"
  "subwayLines": [ '1', '2', '3', '4', '5', '6', 'N', 'R', 'E', 'J' ]
  "nearby": [ 'Battery Park City', 'Tribeca', 'Chinatown', 'Lower East Side' ]
  "borough": "Manhattan"
  "state": "New York"
  "zipCodes": [ 12345, 54321 ]
}

```

## sources
[All Neighborhoods by Borough - Baruch CUNY](https://www.baruch.cuny.edu/nycdata/population-geography/neighborhoods.htm)

**webscrapers (python)** \
[Webscraper for Zip Codes](https://www.google.com) \
[Webscraper for Subway Lines + Nearby Neighborhoods](https://www.google.com)
