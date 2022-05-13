import React from 'react';
import './styles/style.less';

import RestTest from './components/RestTest';


const Main = () => (
    <>
      <img src="/assets/icon.png" />
      <h1>Sample React application is working!</h1>
      <RestTest />
      <p>See api documentation <a href="/api/ui/">here</a></p>
    </>
);

export default Main;