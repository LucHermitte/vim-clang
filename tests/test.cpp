struct S {
    void f(int i, float);
    void g(double d) const;
    void h(double d) volatile; // cannot detect volatile...
    constexpr void i(double d) ;

    virtual int pure() = 0;
    virtual int v();

    template <typename T, std::size_t N> t(T element, unsigned u);

    S() = default;
};

struct S2 {
    int v() override;
    int pure() final;
};
