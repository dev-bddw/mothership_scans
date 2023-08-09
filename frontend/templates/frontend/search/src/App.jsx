import {useRef, useState, useEffect} from 'react'

function App() {

  return(
    <div>
      <Search/>
    </div>
  )
}

function Search() {

  const [search, setSearch] = useState('')
  const [scans, setScans] = useState(CONTEXT.scans)

  function onChangeHandler(event) {
    setSearch(event.target.value)
  }
	const isMounted = useRef(false)
	const total_scans = useRef(CONTEXT.scans.length)
  const is_empty = scans.length == 0

  function match(scan) {
//    .filter(i => (i && i.user && i.user.includes(this.searchUser)))

    return (
      ( scan && scan.sku && scan.sku.includes(search) )
      || (scan && scan.location && scan.location.includes(search))
      || (scan && scan.scan_id && scan.scan_id.includes(search) )
      || (scan && scan.tracking && scan.tracking.includes(search))
      || (scan && scan.sku && scan.sku.includes(search.toUpperCase()) )
      || (scan && scan.location && scan.location.includes(search.toUpperCase()))
      || (scan && scan.scan_id && scan.scan_id.includes(search.toUpperCase()))
      || (scan && scan.tracking && scan.tracking.includes(search.toUpperCase()))
    )
  }


  useEffect(() => {
    const delayDebounceFn = setTimeout( () => {
			if (isMounted.current) {
			  ///SEARCH()
        // filter scans by search
        setScans( CONTEXT.scans.filter( (scan) => match(scan) ) )
			} else {
					isMounted.current = true
				}
    }, 100)
		return( () => clearTimeout(delayDebounceFn) )
  }, [search])

//  DEPRECATED
 //  // function for making api call
	// const SEARCH = () => {
	// 	fetch(CONTEXT.search_api, {
	// 		credentials: 'include',
	// 		mode: 'same-origin',
	// 		method: "POST",
	// 		headers: {
	// 	    "Content-Type": "application/json",
	// 			"Accept": 'application/json',
	// 			'Authorization': `Token ${CONTEXT.auth_token}`,
	// 			'X-CSRFToken': CONTEXT.csrf_token
 //        },
	// 		body: JSON.stringify( {'data': { search } } ),
	// 				})
	// 					.then(response => response.json())
	// 					.then(data => {
 //              setScans(data.data)
	// 						console.log(data.data);
	// 					})
	// }
	//

  return (
    <div className="w-full">
    <div style={{'margin-bottom': '40px'}} className="heading grid grid-cols-1 text-center">
        <div className="text-gray-800" style={{'font-size': '50px'}}>
          BDDW SCANS
        </div>
        <div className={'underline'} style={{'font-size': '20px'}}>ALL SCANS DISPLAY EST TIME</div>
      </div>
      <div className="grid grid cols-1 justify-center">
          <label for="default-search" className="mb-2 text-sm font-medium text-gray-900 sr-only dark:text-white">Search</label>
          <div className="relative">
              <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                  <svg aria-hidden="true" className="w-5 h-5 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
              </div>
              <input style={{'width': '500px'}} onChange={ (event)=> onChangeHandler(event)} value={search} type="search" id="default-search" className="p-2 pl-10 text-sm text-gray-900 border border-gray-300 rounded-lg bg-gray-50 focus:ring-blue-500 focus:border-blue-500" placeholder="Search scans by sku, tracking, scan id" required/>
          </div>
      <div className="text-start py-3 text-gray-500 text-sm">Displaying {scans.length} of {total_scans.current} scans...</div>
      <div className="relative overflow-x-auto shadow-md sm:rounded-lg">
          <table className="border rounded text-sm text-left text-gray-500">
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
              <tr className="border-b bg-white">
                <td style={{width: '170px'}} className={'py-2 px-3'}>Returned None</td>
                <td style={{width: '170px'}} className={'py-2 px-3'}></td>
                <td style={{width: '170px'}} className={'py-2 px-3'}></td>
                <td style={{width: '200px'}} className={'py-2 px-3'}></td>
                <td style={{width: '200px'}} className={'py-2 px-3'}></td>
                <td style={{width: '370px'}} className={'py-2 px-3'}></td>
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
    <tr key={scan.id} className="hover:bg-gray-50 border-b">
      <td style={{width: '170px'}} onClick={() => onClickHandler(scan.sku)} className={'py-2 px-3'}>
        <div className={'cursor-pointer hover:underline'}>{scan.sku}</div>
      </td>
      <td style={{width: '170px'}} onClick={() => onClickHandler(scan.tracking)} className={'py-2 px-3'}>
        <div className={'cursor-pointer hover:underline'}>{scan.tracking}</div>
      </td>
      <td style={{width: '170px'}} onClick={() => onClickHandler(scan.location)} className={'py-2 px-3'}>
        <div className={'cursor-pointer hover:underline'}>{scan.location}</div>
      </td>
      <td style={{width: '200px'}} className={'py-2 px-3'}>{scan.time_scan}</td>
      <td style={{width: '200px'}} className={'py-2 px-3'}>{scan.time_upload}</td>
      <td style={{width: '370px'}} onClick={() => onClickHandler(scan.scan_id)} className={'py-2 px-3'}>
        <div className={'cursor-pointer hover:underline'}>{scan.scan_id}</div>
      </td>
      <td style={{width: '165px'}} className={'py-2 px-3'}>{ scan.bin_success ? 'SUCCESS' : <span className="text-red-400">FAILED</span>}</td>
  </tr>

  )
}
