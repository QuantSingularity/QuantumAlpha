import React from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  StatusBar,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import LinearGradient from "react-native-linear-gradient";
import Icon from "react-native-vector-icons/MaterialCommunityIcons";
import * as Animatable from "react-native-animatable";
import { useNavigation } from "@react-navigation/native";
import { useTheme } from "../../context/ThemeContext";
import { Wordmark } from "../../components/brand/Logo";

const features = [
  {
    icon: "brain",
    title: "Adaptive AI strategies",
    body: "Models retrain on live order flow so your edge adapts instead of decaying.",
  },
  {
    icon: "shield-check",
    title: "Real-time risk engine",
    body: "VaR, CVaR, and stress scenarios recompute on every fill, with automatic guardrails.",
  },
  {
    icon: "lightning-bolt",
    title: "Microsecond execution",
    body: "Smart order routing minimises slippage and captures the best available price.",
  },
  {
    icon: "chart-line-variant",
    title: "Quant-grade analytics",
    body: "Attribution, factor exposure, and drawdown analysis the way a desk reads them.",
  },
];

const ticker = [
  { s: "AAPL", c: "+1.33%", up: true },
  { s: "MSFT", c: "+1.39%", up: true },
  { s: "NVDA", c: "+3.02%", up: true },
  { s: "TSLA", c: "-3.31%", up: false },
];

const HomeScreen = () => {
  const navigation = useNavigation();
  const { theme } = useTheme();
  const styles = makeStyles(theme);

  return (
    <View style={{ flex: 1, backgroundColor: theme.background }}>
      <StatusBar barStyle="light-content" backgroundColor={theme.background} />
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: 40 }}
      >
        {/* Hero */}
        <LinearGradient
          colors={[
            "rgba(34,211,238,0.14)",
            "rgba(10,16,32,0.4)",
            "transparent",
          ]}
          start={{ x: 0.5, y: 0 }}
          end={{ x: 0.5, y: 1 }}
          style={styles.hero}
        >
          <SafeAreaView edges={["top"]}>
            <View style={styles.navRow}>
              <Wordmark size={28} />
              <TouchableOpacity onPress={() => navigation.navigate("Login")}>
                <Text style={styles.navLink}>Sign in</Text>
              </TouchableOpacity>
            </View>

            <Animatable.View
              animation="fadeInUp"
              duration={700}
              delay={100}
              style={styles.heroBody}
            >
              <View style={styles.badge}>
                <Icon name="star-four-points" size={13} color={theme.primary} />
                <Text style={styles.badgeText}>Quantum-enhanced execution</Text>
              </View>
              <Text style={styles.heroTitle}>
                Trade with a{" "}
                <Text style={{ color: theme.primary }}>quantum edge</Text>
              </Text>
              <Text style={styles.heroSub}>
                Adaptive AI strategies, a real-time risk engine, and
                institutional execution - in one terminal built for serious
                traders.
              </Text>

              <TouchableOpacity
                activeOpacity={0.9}
                onPress={() => navigation.navigate("Register")}
              >
                <LinearGradient
                  colors={theme.gradient}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={styles.primaryBtn}
                >
                  <Text style={styles.primaryBtnText}>Get started free</Text>
                  <Icon name="arrow-right" size={18} color="#060A14" />
                </LinearGradient>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.secondaryBtn}
                onPress={() => navigation.navigate("Login")}
              >
                <Text style={styles.secondaryBtnText}>
                  I already have an account
                </Text>
              </TouchableOpacity>
            </Animatable.View>

            {/* Ticker */}
            <Animatable.View
              animation="fadeIn"
              delay={400}
              style={styles.ticker}
            >
              {ticker.map((t) => (
                <View key={t.s} style={styles.tickerItem}>
                  <Text style={styles.tickerSym}>{t.s}</Text>
                  <Text
                    style={[
                      styles.tickerChg,
                      { color: t.up ? theme.success : theme.error },
                    ]}
                  >
                    {t.c}
                  </Text>
                </View>
              ))}
            </Animatable.View>
          </SafeAreaView>
        </LinearGradient>

        {/* Features */}
        <View style={styles.section}>
          <Text style={styles.eyebrow}>THE PLATFORM</Text>
          <Text style={styles.sectionTitle}>Everything a desk needs</Text>
          <View style={styles.featureGrid}>
            {features.map((f, i) => (
              <Animatable.View
                key={f.title}
                animation="fadeInUp"
                delay={i * 90}
                style={styles.featureCard}
              >
                <View style={styles.featureIcon}>
                  <Icon name={f.icon} size={20} color={theme.primary} />
                </View>
                <Text style={styles.featureTitle}>{f.title}</Text>
                <Text style={styles.featureBody}>{f.body}</Text>
              </Animatable.View>
            ))}
          </View>
        </View>

        {/* Stats */}
        <View style={styles.statsRow}>
          {[
            ["$4.8B+", "Routed"],
            ["128K", "Accounts"],
            ["99.99%", "Uptime"],
          ].map(([v, l]) => (
            <View key={l} style={styles.statItem}>
              <Text style={styles.statValue}>{v}</Text>
              <Text style={styles.statLabel}>{l}</Text>
            </View>
          ))}
        </View>

        {/* CTA */}
        <View style={styles.section}>
          <LinearGradient
            colors={[theme.surface, theme.card]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.cta}
          >
            <Text style={styles.ctaTitle}>Ready to find your alpha?</Text>
            <Text style={styles.ctaSub}>Set up your terminal in minutes.</Text>
            <TouchableOpacity
              activeOpacity={0.9}
              onPress={() => navigation.navigate("Register")}
            >
              <LinearGradient
                colors={theme.gradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.primaryBtn}
              >
                <Text style={styles.primaryBtnText}>Create free account</Text>
              </LinearGradient>
            </TouchableOpacity>
          </LinearGradient>
        </View>

        <Text style={styles.footer}>
          © {new Date().getFullYear()} QuantumAlpha · For demonstration only
        </Text>
      </ScrollView>
    </View>
  );
};

const makeStyles = (theme) =>
  StyleSheet.create({
    hero: { paddingHorizontal: 20, paddingBottom: 28 },
    navRow: {
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "space-between",
      paddingTop: 8,
    },
    navLink: { color: theme.textSecondary, fontWeight: "600", fontSize: 15 },
    heroBody: { marginTop: 48, alignItems: "center" },
    badge: {
      flexDirection: "row",
      alignItems: "center",
      gap: 6,
      backgroundColor: "rgba(34,211,238,0.08)",
      borderColor: theme.border,
      borderWidth: 1,
      paddingHorizontal: 12,
      paddingVertical: 6,
      borderRadius: 999,
      marginBottom: 20,
    },
    badgeText: {
      color: theme.text,
      fontSize: 12,
      fontWeight: "600",
      marginLeft: 6,
    },
    heroTitle: {
      color: theme.text,
      fontSize: 40,
      fontWeight: "800",
      textAlign: "center",
      lineHeight: 46,
      letterSpacing: -1,
    },
    heroSub: {
      color: theme.textSecondary,
      fontSize: 15.5,
      textAlign: "center",
      lineHeight: 23,
      marginTop: 16,
      marginBottom: 28,
      paddingHorizontal: 8,
    },
    primaryBtn: {
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "center",
      gap: 8,
      paddingVertical: 15,
      paddingHorizontal: 28,
      borderRadius: 14,
      minWidth: 240,
    },
    primaryBtnText: {
      color: "#060A14",
      fontWeight: "800",
      fontSize: 16,
      marginRight: 8,
    },
    secondaryBtn: { marginTop: 14, paddingVertical: 8 },
    secondaryBtnText: {
      color: theme.textSecondary,
      fontWeight: "600",
      fontSize: 14.5,
    },
    ticker: {
      flexDirection: "row",
      justifyContent: "space-between",
      marginTop: 36,
      backgroundColor: theme.card,
      borderColor: theme.border,
      borderWidth: 1,
      borderRadius: 14,
      paddingVertical: 14,
      paddingHorizontal: 6,
    },
    tickerItem: { flex: 1, alignItems: "center" },
    tickerSym: { color: theme.textSecondary, fontSize: 12, marginBottom: 4 },
    tickerChg: { fontFamily: theme.fontMono, fontWeight: "700", fontSize: 13 },
    section: { paddingHorizontal: 20, marginTop: 36 },
    eyebrow: {
      color: theme.textSecondary,
      fontSize: 11,
      fontWeight: "800",
      letterSpacing: 2,
    },
    sectionTitle: {
      color: theme.text,
      fontSize: 24,
      fontWeight: "800",
      marginTop: 6,
      marginBottom: 18,
      letterSpacing: -0.5,
    },
    featureGrid: {
      flexDirection: "row",
      flexWrap: "wrap",
      justifyContent: "space-between",
    },
    featureCard: {
      width: "48%",
      backgroundColor: theme.card,
      borderColor: theme.border,
      borderWidth: 1,
      borderRadius: 16,
      padding: 16,
      marginBottom: 14,
    },
    featureIcon: {
      width: 40,
      height: 40,
      borderRadius: 10,
      backgroundColor: "rgba(34,211,238,0.12)",
      alignItems: "center",
      justifyContent: "center",
      marginBottom: 12,
    },
    featureTitle: {
      color: theme.text,
      fontWeight: "700",
      fontSize: 14.5,
      marginBottom: 6,
    },
    featureBody: { color: theme.textSecondary, fontSize: 12.5, lineHeight: 18 },
    statsRow: {
      flexDirection: "row",
      justifyContent: "space-around",
      marginTop: 36,
      marginHorizontal: 20,
      paddingVertical: 22,
      borderTopWidth: 1,
      borderBottomWidth: 1,
      borderColor: theme.border,
    },
    statItem: { alignItems: "center" },
    statValue: {
      color: theme.primary,
      fontFamily: theme.fontMono,
      fontSize: 24,
      fontWeight: "800",
    },
    statLabel: { color: theme.textSecondary, fontSize: 12, marginTop: 4 },
    cta: {
      borderRadius: 22,
      padding: 28,
      alignItems: "center",
      borderWidth: 1,
      borderColor: theme.border,
    },
    ctaTitle: {
      color: theme.text,
      fontSize: 22,
      fontWeight: "800",
      textAlign: "center",
    },
    ctaSub: {
      color: theme.textSecondary,
      fontSize: 14,
      marginTop: 8,
      marginBottom: 20,
    },
    footer: {
      color: theme.textMuted,
      fontSize: 12,
      textAlign: "center",
      marginTop: 32,
    },
  });

export default HomeScreen;
