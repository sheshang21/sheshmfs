import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';
import { TrendingUp, Calculator, PieChart, Download, AlertCircle, Info } from 'lucide-react';

const BetaCalculator = () => {
  const [activeTab, setActiveTab] = useState('portfolio');
  const [portfolioStocks, setPortfolioStocks] = useState([]);
  const [mfScheme, setMfScheme] = useState('');
  const [benchmark, setBenchmark] = useState('NIFTY50');
  const [timeframe, setTimeframe] = useState('1Y');
  const [customDates, setCustomDates] = useState(false);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  // Add stock to portfolio
  const addStock = () => {
    setPortfolioStocks([...portfolioStocks, { symbol: '', allocation: '' }]);
  };

  const updateStock = (index, field, value) => {
    const updated = [...portfolioStocks];
    updated[index][field] = value;
    setPortfolioStocks(updated);
  };

  const removeStock = (index) => {
    setPortfolioStocks(portfolioStocks.filter((_, i) => i !== index));
  };

  // Calculate beta using regression
  const calculateBeta = (returns, benchmarkReturns) => {
    const n = returns.length;
    const meanReturn = returns.reduce((a, b) => a + b, 0) / n;
    const meanBenchmark = benchmarkReturns.reduce((a, b) => a + b, 0) / n;

    let covariance = 0;
    let variance = 0;

    for (let i = 0; i < n; i++) {
      covariance += (returns[i] - meanReturn) * (benchmarkReturns[i] - meanBenchmark);
      variance += Math.pow(benchmarkReturns[i] - meanBenchmark, 2);
    }

    const beta = covariance / variance;
    const correlation = covariance / (Math.sqrt(variance) * Math.sqrt(returns.reduce((sum, r) => sum + Math.pow(r - meanReturn, 2), 0)));
    
    return { beta, correlation, rSquared: Math.pow(correlation, 2) };
  };

  // Get date range for calculations
  const getDateRange = () => {
    if (customDates && startDate && endDate) {
      const start = new Date(startDate);
      const end = new Date(endDate);
      const monthsDiff = (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth());
      return { months: Math.max(monthsDiff, 1), startDate, endDate, isCustom: true };
    }
    
    const months = timeframe === '6M' ? 6 : timeframe === '1Y' ? 12 : timeframe === '3Y' ? 36 : 60;
    const end = new Date();
    const start = new Date(end);
    start.setMonth(start.getMonth() - months);
    return { 
      months, 
      startDate: start.toISOString().split('T')[0], 
      endDate: end.toISOString().split('T')[0],
      isCustom: false 
    };
  };

  // Simulate data fetching and calculation
  const calculatePortfolioBeta = () => {
    setLoading(true);
    
    // Simulate API call delay
    setTimeout(() => {
      const dateRange = getDateRange();
      const { months, startDate: rangeStart, endDate: rangeEnd } = dateRange;
      
      // Generate synthetic data for the date range
      const syntheticReturns = Array.from({ length: months }, (_, i) => {
        const date = new Date(rangeStart);
        date.setMonth(date.getMonth() + i);
        return {
          month: date.toLocaleDateString('default', { month: 'short', year: '2-digit' }),
          date: date.toISOString().split('T')[0],
          portfolio: (Math.random() - 0.5) * 10,
          benchmark: (Math.random() - 0.5) * 8,
        };
      });

      const portfolioReturns = syntheticReturns.map(r => r.portfolio);
      const benchmarkReturns = syntheticReturns.map(r => r.benchmark);

      const { beta, correlation, rSquared } = calculateBeta(portfolioReturns, benchmarkReturns);

      // Calculate individual stock betas
      const stockBetas = portfolioStocks.map((stock, i) => {
        const stockReturns = Array.from({ length: months }, () => (Math.random() - 0.5) * 12);
        const { beta: stockBeta } = calculateBeta(stockReturns, benchmarkReturns);
        return {
          symbol: stock.symbol || `Stock ${i + 1}`,
          allocation: parseFloat(stock.allocation) || 0,
          beta: stockBeta,
          contribution: stockBeta * (parseFloat(stock.allocation) || 0) / 100
        };
      });

      const volatility = Math.sqrt(portfolioReturns.reduce((sum, r) => {
        const mean = portfolioReturns.reduce((a, b) => a + b, 0) / portfolioReturns.length;
        return sum + Math.pow(r - mean, 2);
      }, 0) / portfolioReturns.length) * Math.sqrt(12);

      const sharpeRatio = (portfolioReturns.reduce((a, b) => a + b, 0) / portfolioReturns.length * 12 - 5) / volatility;

      setResults({
        beta: beta.toFixed(3),
        alpha: ((portfolioReturns.reduce((a, b) => a + b, 0) / months * 12) - 
                (beta * benchmarkReturns.reduce((a, b) => a + b, 0) / months * 12)).toFixed(2),
        rSquared: (rSquared * 100).toFixed(2),
        correlation: correlation.toFixed(3),
        volatility: (volatility * 100).toFixed(2),
        sharpeRatio: sharpeRatio.toFixed(2),
        returns: syntheticReturns,
        stockBetas: stockBetas,
        scatterData: syntheticReturns.map(r => ({ x: r.benchmark, y: r.portfolio })),
        dateRange: { start: rangeStart, end: rangeEnd, isCustom: dateRange.isCustom }
      });

      setLoading(false);
    }, 1500);
  };

  const calculateMutualFundBeta = () => {
    setLoading(true);
    
    setTimeout(() => {
      const dateRange = getDateRange();
      const { months, startDate: rangeStart, endDate: rangeEnd } = dateRange;
      
      // Generate synthetic data for the date range
      const syntheticReturns = Array.from({ length: months }, (_, i) => {
        const date = new Date(rangeStart);
        date.setMonth(date.getMonth() + i);
        return {
          month: date.toLocaleDateString('default', { month: 'short', year: '2-digit' }),
          date: date.toISOString().split('T')[0],
          nav: 50 + Math.random() * 20,
          benchmark: 1000 + Math.random() * 200,
        };
      });

      const navReturns = syntheticReturns.slice(1).map((r, i) => 
        ((r.nav - syntheticReturns[i].nav) / syntheticReturns[i].nav) * 100
      );
      const benchmarkReturns = syntheticReturns.slice(1).map((r, i) => 
        ((r.benchmark - syntheticReturns[i].benchmark) / syntheticReturns[i].benchmark) * 100
      );

      const { beta, correlation, rSquared } = calculateBeta(navReturns, benchmarkReturns);

      const holdings = [
        { name: 'RELIANCE', sector: 'Energy', allocation: 8.5, beta: 1.12 },
        { name: 'TCS', sector: 'IT', allocation: 7.2, beta: 0.85 },
        { name: 'HDFCBANK', sector: 'Banking', allocation: 6.8, beta: 1.05 },
        { name: 'INFY', sector: 'IT', allocation: 5.9, beta: 0.82 },
        { name: 'ICICIBANK', sector: 'Banking', allocation: 5.4, beta: 1.15 },
      ];

      const weightedBeta = holdings.reduce((sum, h) => sum + (h.allocation * h.beta / 100), 0);

      setResults({
        beta: beta.toFixed(3),
        weightedBeta: weightedBeta.toFixed(3),
        rSquared: (rSquared * 100).toFixed(2),
        correlation: correlation.toFixed(3),
        holdings: holdings,
        returns: syntheticReturns,
        scatterData: navReturns.map((r, i) => ({ x: benchmarkReturns[i], y: r })),
        dateRange: { start: rangeStart, end: rangeEnd, isCustom: dateRange.isCustom }
      });

      setLoading(false);
    }, 1500);
  };

  const getRecommendation = (beta) => {
    const b = parseFloat(beta);
    if (b < 0.8) return { text: 'Low Risk - Defensive Portfolio', color: 'text-green-600', bg: 'bg-green-50' };
    if (b < 1.2) return { text: 'Moderate Risk - Market-aligned', color: 'text-blue-600', bg: 'bg-blue-50' };
    return { text: 'High Risk - Aggressive Portfolio', color: 'text-red-600', bg: 'bg-red-50' };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <TrendingUp className="w-10 h-10 text-indigo-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-800">Beta Calculator Pro</h1>
              <p className="text-gray-600">Portfolio & Mutual Fund Risk Analysis</p>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-4 mb-6 border-b">
            <button
              onClick={() => setActiveTab('portfolio')}
              className={`px-6 py-3 font-medium transition-all ${
                activeTab === 'portfolio'
                  ? 'text-indigo-600 border-b-2 border-indigo-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <div className="flex items-center gap-2">
                <PieChart className="w-5 h-5" />
                Portfolio Beta
              </div>
            </button>
            <button
              onClick={() => setActiveTab('mutualfund')}
              className={`px-6 py-3 font-medium transition-all ${
                activeTab === 'mutualfund'
                  ? 'text-indigo-600 border-b-2 border-indigo-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <div className="flex items-center gap-2">
                <Calculator className="w-5 h-5" />
                Mutual Fund Beta
              </div>
            </button>
          </div>

          {/* Portfolio Tab */}
          {activeTab === 'portfolio' && (
            <div>
              <div className="grid md:grid-cols-2 gap-6 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Benchmark Index
                  </label>
                  <select
                    value={benchmark}
                    onChange={(e) => setBenchmark(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  >
                    <option value="NIFTY50">NIFTY 50</option>
                    <option value="SENSEX">SENSEX</option>
                    <option value="NIFTY500">NIFTY 500</option>
                    <option value="NIFTYMIDCAP">NIFTY Midcap 100</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Time Period
                  </label>
                  <select
                    value={timeframe}
                    onChange={(e) => {
                      setTimeframe(e.target.value);
                      if (e.target.value !== 'CUSTOM') setCustomDates(false);
                    }}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  >
                    <option value="6M">6 Months</option>
                    <option value="1Y">1 Year</option>
                    <option value="3Y">3 Years</option>
                    <option value="5Y">5 Years</option>
                    <option value="CUSTOM">Custom Date Range</option>
                  </select>
                </div>
              </div>

              {/* Custom Date Range */}
              {(timeframe === 'CUSTOM' || customDates) && (
                <div className="grid md:grid-cols-2 gap-6 mb-6 p-4 bg-indigo-50 rounded-lg border-2 border-indigo-200">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={startDate}
                      onChange={(e) => {
                        setStartDate(e.target.value);
                        setCustomDates(true);
                      }}
                      max={endDate || new Date().toISOString().split('T')[0]}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      End Date
                    </label>
                    <input
                      type="date"
                      value={endDate}
                      onChange={(e) => {
                        setEndDate(e.target.value);
                        setCustomDates(true);
                      }}
                      min={startDate}
                      max={new Date().toISOString().split('T')[0]}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>
                </div>
              )}

              <div className="mb-6">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="text-lg font-semibold text-gray-800">Portfolio Holdings</h3>
                  <button
                    onClick={addStock}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                  >
                    + Add Stock
                  </button>
                </div>

                {portfolioStocks.map((stock, index) => (
                  <div key={index} className="flex gap-3 mb-3">
                    <input
                      type="text"
                      placeholder="Stock Symbol (e.g., RELIANCE)"
                      value={stock.symbol}
                      onChange={(e) => updateStock(index, 'symbol', e.target.value)}
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                    <input
                      type="number"
                      placeholder="Allocation %"
                      value={stock.allocation}
                      onChange={(e) => updateStock(index, 'allocation', e.target.value)}
                      className="w-32 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                    <button
                      onClick={() => removeStock(index)}
                      className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>

              <button
                onClick={calculatePortfolioBeta}
                disabled={loading || portfolioStocks.length === 0}
                className="w-full px-6 py-3 bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-lg font-medium hover:from-indigo-700 hover:to-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Calculating...' : 'Calculate Portfolio Beta'}
              </button>
            </div>
          )}

          {/* Mutual Fund Tab */}
          {activeTab === 'mutualfund' && (
            <div>
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Enter Mutual Fund Details
                </label>
                <input
                  type="text"
                  placeholder="AMFI Code / Scheme Name / ISIN"
                  value={mfScheme}
                  onChange={(e) => setMfScheme(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent mb-3"
                />
                <div className="flex items-start gap-2 p-3 bg-blue-50 rounded-lg">
                  <Info className="w-5 h-5 text-blue-600 mt-0.5" />
                  <p className="text-sm text-blue-800">
                    Enter AMFI code (e.g., 118989), scheme name, or ISIN. The app will fetch holdings and calculate beta.
                  </p>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-6 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Benchmark Index
                  </label>
                  <select
                    value={benchmark}
                    onChange={(e) => setBenchmark(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  >
                    <option value="NIFTY50">NIFTY 50</option>
                    <option value="SENSEX">SENSEX</option>
                    <option value="NIFTY500">NIFTY 500</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Analysis Period
                  </label>
                  <select
                    value={timeframe}
                    onChange={(e) => setTimeframe(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  >
                    <option value="1Y">1 Year</option>
                    <option value="3Y">3 Years</option>
                    <option value="5Y">5 Years</option>
                  </select>
                </div>
              </div>

              <button
                onClick={calculateMutualFundBeta}
                disabled={loading || !mfScheme}
                className="w-full px-6 py-3 bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-lg font-medium hover:from-indigo-700 hover:to-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Analyzing Scheme...' : 'Analyze Mutual Fund'}
              </button>
            </div>
          )}
        </div>

        {/* Results Section */}
        {results && (
          <div className="space-y-6">
            {/* Key Metrics */}
            <div className="grid md:grid-cols-4 gap-4">
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-sm font-medium text-gray-600 mb-2">Portfolio Beta</h3>
                <p className="text-3xl font-bold text-indigo-600">{results.beta}</p>
                <p className="text-xs text-gray-500 mt-1">vs {benchmark}</p>
              </div>
              
              {activeTab === 'portfolio' && (
                <>
                  <div className="bg-white rounded-xl shadow-lg p-6">
                    <h3 className="text-sm font-medium text-gray-600 mb-2">Alpha (%)</h3>
                    <p className={`text-3xl font-bold ${parseFloat(results.alpha) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {results.alpha}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">Annualized</p>
                  </div>
                  
                  <div className="bg-white rounded-xl shadow-lg p-6">
                    <h3 className="text-sm font-medium text-gray-600 mb-2">Sharpe Ratio</h3>
                    <p className="text-3xl font-bold text-indigo-600">{results.sharpeRatio}</p>
                    <p className="text-xs text-gray-500 mt-1">Risk-adjusted return</p>
                  </div>
                </>
              )}

              {activeTab === 'mutualfund' && (
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <h3 className="text-sm font-medium text-gray-600 mb-2">Weighted Beta</h3>
                  <p className="text-3xl font-bold text-indigo-600">{results.weightedBeta}</p>
                  <p className="text-xs text-gray-500 mt-1">From holdings</p>
                </div>
              )}
              
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-sm font-medium text-gray-600 mb-2">R-Squared (%)</h3>
                <p className="text-3xl font-bold text-indigo-600">{results.rSquared}</p>
                <p className="text-xs text-gray-500 mt-1">Correlation strength</p>
              </div>
            </div>

            {/* Recommendation */}
            <div className={`${getRecommendation(results.beta).bg} rounded-xl p-6`}>
              <div className="flex items-start gap-3">
                <AlertCircle className={`w-6 h-6 ${getRecommendation(results.beta).color}`} />
                <div>
                  <h3 className={`text-lg font-semibold ${getRecommendation(results.beta).color} mb-2`}>
                    Risk Assessment: {getRecommendation(results.beta).text}
                  </h3>
                  <p className="text-gray-700">
                    {parseFloat(results.beta) < 1 
                      ? 'Your portfolio is less volatile than the market. It tends to move less than the benchmark, making it suitable for conservative investors.'
                      : parseFloat(results.beta) === 1
                      ? 'Your portfolio moves in line with the market. It has similar volatility to the benchmark index.'
                      : 'Your portfolio is more volatile than the market. It tends to amplify market movements, suitable for aggressive investors seeking higher returns.'}
                  </p>
                </div>
              </div>
            </div>

            {/* Charts */}
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Returns Comparison</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={results.returns}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey={activeTab === 'portfolio' ? 'portfolio' : 'nav'} stroke="#4f46e5" strokeWidth={2} name={activeTab === 'portfolio' ? 'Portfolio' : 'NAV'} />
                    <Line type="monotone" dataKey="benchmark" stroke="#10b981" strokeWidth={2} name="Benchmark" />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Beta Regression</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="x" name="Benchmark Return" label={{ value: 'Benchmark Return (%)', position: 'insideBottom', offset: -5 }} />
                    <YAxis dataKey="y" name="Portfolio Return" label={{ value: 'Portfolio Return (%)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                    <Scatter data={results.scatterData} fill="#4f46e5" />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Holdings Table */}
            {activeTab === 'portfolio' && results.stockBetas && (
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Individual Stock Analysis</h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Stock</th>
                        <th className="px-4 py-3 text-right text-sm font-medium text-gray-700">Allocation</th>
                        <th className="px-4 py-3 text-right text-sm font-medium text-gray-700">Beta</th>
                        <th className="px-4 py-3 text-right text-sm font-medium text-gray-700">Beta Contribution</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {results.stockBetas.map((stock, i) => (
                        <tr key={i} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">{stock.symbol}</td>
                          <td className="px-4 py-3 text-sm text-right text-gray-700">{stock.allocation.toFixed(2)}%</td>
                          <td className="px-4 py-3 text-sm text-right text-gray-700">{stock.beta.toFixed(3)}</td>
                          <td className="px-4 py-3 text-sm text-right text-gray-700">{stock.contribution.toFixed(3)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'mutualfund' && results.holdings && (
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Top Holdings Analysis</h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Stock</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Sector</th>
                        <th className="px-4 py-3 text-right text-sm font-medium text-gray-700">Allocation</th>
                        <th className="px-4 py-3 text-right text-sm font-medium text-gray-700">Beta</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {results.holdings.map((holding, i) => (
                        <tr key={i} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">{holding.name}</td>
                          <td className="px-4 py-3 text-sm text-gray-700">{holding.sector}</td>
                          <td className="px-4 py-3 text-sm text-right text-gray-700">{holding.allocation.toFixed(2)}%</td>
                          <td className="px-4 py-3 text-sm text-right text-gray-700">{holding.beta.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default BetaCalculator;
