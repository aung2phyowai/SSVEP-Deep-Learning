%% EEG Topographic Map generation
% S2 (SJ)
clear;clc;close all;
% S1_ds (Ref at Oz)
% Data = [ 1941.85350398  1726.06321824  1841.25723102  2172.10605732  2217.56082748 2184.63523263  2122.80802037  2276.35576658  2257.81298929  2514.12508408 2529.57014231  2601.16240518  2519.41851376  2643.26595424  2582.148321 2681.28015086  2723.62955054  2933.64455759  2602.00893494  2569.34303632 2544.813744    2467.01590308  2255.96239576  2389.11012008  2291.29073653 2168.88022826  1906.30696024  2190.75858848  2048.92608516  2150.45084315 1988.03958219  2296.3960979] ;
% S1_ds_avgRef
% Data = [ 2226.05097828  2323.00700815  2494.57273567  2539.86941516  2552.45061977 2460.01463324  2495.17338948  2609.57910865  2748.76275508  2682.86936653 2654.2231577   2624.94420424  2602.02289553  2487.78164812  2560.35612621 2696.69399151  2818.1367927   2807.10037725  2774.89146784  2573.95268636 2859.84648316  2765.57654062  2676.49635005  2468.97917916  2317.25508187 2230.46966426  2260.40841232  2250.12837795  2022.888876    1924.3312659 2096.62449855  2121.07319154];
% S2_ds (Ref @ Oz); 
% Data = [ 1985.25660828  2001.91799312  2031.33203998  2004.67568912  2052.82510755 1847.25605612  1792.42173693  1976.10480542  1917.31985622  1985.79977911 2193.81978264  1921.56808699  2131.57680599  2132.11984311  2095.39330558 2250.29222481  1925.0509329   1637.85217637  1974.49286258  2088.48053663 2030.62417315  2198.20577806  1521.21980705  1652.63829585  1554.26237323 1532.37612773  1555.8325268   1623.70696761  1473.00418967  1391.31572838 1620.96573788  1633.78155875];
% S2_decimate (Ref @ Oz); 
Data = [ 2435.575871 2237.91486341 2068.1178718 2468.34623286 2481.59850953 2498.89865449 2373.75806294 2548.76958338 2418.98067058 2485.40795195 2773.45963218 2517.71413181 2615.79413587 2617.17885592 2551.16368065 2556.56446707 2706.29138487 2836.21446408 2642.94875399 2709.86758826 2445.75058623 2458.041481 2416.35328785 1960.69008772 2213.99585409 2121.69283558 1873.4222457 2130.12539785 2123.93589284 1904.73689047 1948.47197426 1990.00522999];
% 2-class S2 decimation c0 and 1
Data = [ 1248.37033381 1466.24867322 1488.85452632 1403.21421049 1495.96982988 1547.84610608 1654.82483771 1717.64423207 1576.21161842 1668.97332333 1800.22565451 1748.08503689 1973.82422567 1776.16846456 2018.32116023 2021.36313935 2002.76938212 1954.8048108 2012.01624581 2015.6583295 1959.16346383 1939.0861572 2073.34297069 2085.65638345 2102.42636577 2075.01585331 2100.76753031 2012.2941358 1974.39410062 1956.99746973 1966.12110636 1960.90221584];
% 2-class S2 decimation c1 and 2
% Data
% 3-class
Data = [ 1667.02387763 1835.65160116 1827.54360487 2005.02786283 2090.84785049 2049.20476838 1992.762206 2052.99547673 1842.52336389 2031.50581513 2022.93621369 1918.48279014 2140.00216914 1931.63577997 2108.20027683 2049.91461505 2305.20082322 2214.80550524 1966.77685311 2062.04679317 2084.83069053 2333.00809668 2179.48698468 2350.87037231 2109.58209603 2055.54884506 2132.31497908 1964.44610385 2014.50512203 1791.8388021 1576.63824961 1685.91696929];
% 4-class 
Data = [ 1528.92321213 1528.13052715 1521.87452184 1644.96905438 1666.18662721 1706.68802777 1429.11153227 1464.46019083 1441.20010701 1540.53590104 1556.07101614 1501.28330777 1537.27376683 1763.44572347 1766.75144344 1685.63086147 2033.40827089 1933.47385945 1801.9019199 1713.00634158 1864.09535731 1943.14383969 1997.15036286 1625.14058183 1758.62446348 1856.67193162 1658.62129414 1614.66017144 1654.02739849 1692.28935625 1954.37247377 1756.28848606]

% 5-class: 
Data = [ 2216.84298705 2482.91226873 2356.47463333 2416.05826419 2636.12854414 2840.93307707 2754.98939529 2684.22938645 2881.61863387 2506.02665311 2812.46088913 2518.14453714 2706.46330607 2741.99889415 2970.48658427 2924.25422554 2812.39933268 2712.86176919 2740.75945188 2529.10256983 2608.40425578 2684.17751782 2793.63679009 2728.48649435 2347.76814392 2710.03765064 2230.85344365 2170.67868208 2064.3705784 1685.25258345 1864.74844922 2077.44931612];
% S1 - 300, 5k 
Data = [3.1405499	3.1204054	3.1036057	3.1125963	3.1472521	3.1199422	3.1292379	3.1631682	3.1632693	3.1590338	3.1553094	3.1611359	3.1620913	3.1570489	3.1429563	3.1448917	3.1425524	3.1609359	3.1647055	3.1597595	3.1665387	3.1654062	3.1686594	3.1576571	3.1437974	3.1548858	3.1447039	3.1335235	3.1495869	3.1533456	3.1510124	3.1556005];
topo_cell = {'Fp1' 'AF3' 'F7 ' 'F3 ' 'FC1' 'FC5' 'T7 ' 'C3 ' 'CP1' 'CP5' 'P7' 'P3' 'Pz'  'PO3' 'O1' 'Oz ' 'O2' 'PO4' 'P4' 'P8 ' 'CP6' 'CP2' 'C4'  'T8' 'FC6' 'FC2' 'F4' 'F8' 'AF4' 'Fp2' 'Fz' 'Cz'}
figure; bar(categorical(topo_cell), rescale_minmax(Data, 0, 1)); ylabel('Weighted Score'); ylim([0,1]);
figure; topoplot(rescale_minmax(Data, -1, 1), 'biosemi32_2.asc','style','map','electrodes','labelpoint'); cb = colorbar;
% figure;topoplot([],'Chan64-setup.asc',[lo.hi],'style','map','electrodes','labelpoint'); %To plot channel locations only


