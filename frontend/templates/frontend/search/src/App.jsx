import {useRef, useState, useEffect} from 'react'

function App() {

  // ATTENTION
  // this app is the frontend search bddwscans.com
  // ATTENTION

  const [search, setSearch] = useState('')
  const [scans, setScans] = useState(CONTEXT.scans)

  function onChangeHandler(event) {
    setSearch(event.target.value)
  }
	const isMounted = useRef(false)
  const is_empty = scans.length == 0

  // if search change, wait a moment, send data to django
  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
			if (isMounted.current) {
			  SEARCH()
			} else {
					isMounted.current = true
				}
    }, 100)
		return( () => clearTimeout(delayDebounceFn) )
  }, [search])

  // function for making api call
	const SEARCH = () => {
		fetch(CONTEXT.search_api, {
			credentials: 'include',
			mode: 'same-origin',
			method: "POST",
			headers: {
		    "Content-Type": "application/json",
				"Accept": 'application/json',
				'Authorization': `Token ${CONTEXT.auth_token}`,
				'X-CSRFToken': CONTEXT.csrf_token
        },
			body: JSON.stringify( {'data': { search } } ),
					})
						.then(response => response.json())
						.then(data => {
              setScans(data.data)
							console.log(data.data);
						})
	}


  return (
    <div className="w-full">

    <div style={{'margin-bottom': '40px'}} className="heading grid grid-cols-1 text-center">
        <div className="text-gray-800" style={{'font-size': '50px'}}>
          BDDW SCANS
        </div>
        <a href='/csv/export-latest' className={'py-2 hover:underline'} style={{'font-size': '14px'}}>CSV LAST UNIQUE BY TN</a>
        <div className={'underline'} style={{'font-size': '20px'}}>ALL SCANS DISPLAY EST TIME</div>
      </div>

      <div className="grid grid cols-1 justify-center">
      <form>
          <label for="default-search" className="mb-2 text-sm font-medium text-gray-900 sr-only dark:text-white">Search</label>
          <div className="relative">
              <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                  <svg aria-hidden="true" className="w-5 h-5 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
              </div>
              <input style={{'width': '500px'}} onChange={ (event)=> onChangeHandler(event)} value={search} type="search" id="default-search" className="p-2 pl-10 text-sm text-gray-900 border border-gray-300 rounded-lg bg-gray-50 focus:ring-blue-500 focus:border-blue-500" placeholder="Search scans by sku, tracking, scan id" required/>
          </div>
      </form>
      <div className="text-start py-3 text-gray-500 text-sm">Displaying {scans.length} results...</div>
      <div className="relative overflow-x-auto shadow-md sm:rounded-lg">
          <table className="border rounded w-1200 text-sm text-left text-gray-500">
              <thead className="text-xs text-gray-400 uppercase bg-gray-50">
              <tr>
                <th className="py-2 px-3">sku</th>
                <th className="py-2 px-3">tracking</th>
                <th className="py-2 px-3">location</th>
                <th className="py-2 px-3">time scanned</th>
                <th className="py-2 px-3">time uploaded</th>
                <th className="py-2 px-3">scan id</th>
                <th className="py-2 px-3">bin updated</th>
              </tr>
             </thead>
              <tbody>
            { is_empty ?
              <tr className="w-full border-b bg-white">
                <td style={{width: '170px'}} className={'py-2 px-3'}>Returned None</td>
                <td style={{width: '170px'}} className={'py-2 px-3'}></td>
                <td style={{width: '170px'}} className={'py-2 px-3'}></td>
                <td style={{width: '170px'}} className={'py-2 px-3'}></td>
                <td style={{width: '170px'}} className={'py-2 px-3'}></td>
                <td style={{width: '170px'}} className={'py-2 px-3'}></td>
                <td style={{width: '165px'}} className={'py-2 px-3'}></td>
              </tr>
              :
               scans.map( (scan) => {
                     return( <ScanRow setSearch={setSearch} scan={scan}/>)
                 }
               )
              }
             </tbody>
          </table>
      </div>
    </div>
</div>
 )
}

export default App

function ScanRow({scan, setSearch}) {

  function onClickHandler(value) {
    setSearch(value)
  }

  return(
    <tr className="hover:bg-gray-50 border-b">
      <td onClick={() => onClickHandler(scan.sku)} className={'py-2 px-3'}>
        <div className={'cursor-pointer hover:underline'}>{scan.sku}</div>
      </td>
      <td onClick={() => onClickHandler(scan.tracking)} className={'py-2 px-3'}>
        <div className={'cursor-pointer hover:underline'}>{scan.tracking}</div>
      </td>
      <td onClick={() => onClickHandler(scan.location)} className={'py-2 px-3'}>
        <div className={'cursor-pointer hover:underline'}>{scan.location}</div>
      </td>
      <td className={'py-2 px-3'}>{scan.time_scan}</td>
      <td className={'py-2 px-3'}>{scan.time_upload}</td>
      <td onClick={() => onClickHandler(scan.scan_id)} className={'py-2 px-3'}>
        <div className={'cursor-pointer hover:underline'}>{scan.scan_id}</div>
      </td>
      <td className={'py-2 px-3'}>{ scan.bin_success ? 'SUCCESS' : <span className="text-red-400">FAILED</span>}</td>
  </tr>

  )
}
