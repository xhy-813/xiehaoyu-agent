declare module 'plotly.js-dist' {
  import Plotly from 'plotly.js'
  export = Plotly
}

declare module 'plotly.js' {
  const Plotly: {
    newPlot(
      div: HTMLElement | string,
      data: any[],
      layout?: any,
      config?: any,
    ): Promise<any>
    react(
      div: HTMLElement | string,
      data: any[],
      layout?: any,
      config?: any,
    ): Promise<any>
    purge(div: HTMLElement | string): void
  }
  export default Plotly
}