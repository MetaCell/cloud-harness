import RestTest from './components/RestTest';
import Version from './components/Version';


const Main = () => (
  <>
    <img src="/logo.png" width="800" />
    <h1>__APP_NAME__ React application is working!</h1>
    <Version />
    <RestTest />
    <p>See api documentation <a href="/api/ui/">here</a></p>
  </>
)


export default Main;
