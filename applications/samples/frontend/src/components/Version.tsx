import React, { useState, useEffect } from 'react';



const Version = () => {
  const [result, setResult] = useState(null);
  useEffect(() => {
    fetch("/proxy/common/api/version", {
      headers: {
        'Accept': 'application/json'
      }
    }).then(r => r.json().then(j => setResult(j)), () => setResult({ data: "API error" }));
  }, []);
    

  return result ? <p>Tag: { result?.tag } - Build: {result?.build} </p> : <p>Backend did not answer</p>
}

export default Version;